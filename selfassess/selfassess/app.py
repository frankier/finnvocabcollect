import quart.flask_patch  # noqa
import orjson
import os
from os.path import join as pjoin
from functools import wraps
import datetime
from werkzeug.utils import secure_filename

from quart import (
    _request_ctx_stack, Quart, request, session, abort, redirect,
    url_for, flash, make_response
)
from quart.templating import render_template
from werkzeug.local import LocalProxy
from .database import (
    Participant, Word, ResponseSlot, Response, SessionLogEntry, SessionEvent
)
from sqlalchemy import select
from sqlalchemy import func
from sqlalchemy.orm import scoped_session
from .utils import get_async_session

app = Quart(__name__)
app.config["SERVER_NAME"] = os.environ["SERVER_NAME"]
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
app.config["UPLOAD_DIR"] = os.environ["UPLOAD_DIR"]


USER_SESSION_KEY = "user_id"
current_user = LocalProxy(lambda: _get_user())
dbsess = scoped_session(
    get_async_session(),
    scopefunc=_request_ctx_stack.__ident_func__
)


async def add_event(event_type):
    dbsess.add(SessionLogEntry(
        type=event_type,
        payload=orjson.dumps({
            "remote_addr": request.remote_addr,
            "user_agent": request.headers.get('User-Agent'),
        })
    ))


async def participant_by_token(token):
    res = (await dbsess.execute(
        select(Participant).
        filter_by(token=token)
    )).scalars().first()
    if res is None:
        return None
    return res


async def _get_user():
    session_id = session.get(USER_SESSION_KEY)
    if session_id is None:
        return None
    return await participant_by_token(session_id)


def user_required(func):
    @wraps(func)
    async def decorated_view(*args, **kwargs):
        if await current_user is None:
            abort(401)
        return await func(*args, **kwargs)
    return decorated_view


@app.context_processor
async def inject_email():
    user = await current_user
    if user is None:
        return {}
    return dict(email=user.email)


@app.route("/start/<token>")
async def start(token):
    participant = await participant_by_token(token)
    if participant is None:
        abort(401)
    if participant.withdraw_date is not None:
        return redirect(url_for("withdrawn"))
    session[USER_SESSION_KEY] = token
    return redirect(url_for("overview"))


_total_words = None


async def get_total_words():
    global _total_words
    if _total_words is None:
        _total_words = (await dbsess.execute(
            select(func.count()).select_from(Word)
        )).scalars().first()
    return _total_words


@app.route("/")
@user_required
async def overview():
    user = await current_user
    proof_uploaded = user.proof_upload_date is not None
    proof_accepted = user.proof_accept_date is not None
    if proof_uploaded and proof_accepted:
        language_proof = "accepted"
    elif proof_uploaded:
        language_proof = "pending"
    else:
        language_proof = "none"
    completed_words = user.next_response
    total_words = await get_total_words()
    return await render_template(
        "overview.html",
        accepted=user.accept_date is not None,
        language_proof=language_proof,
        completed_words=completed_words,
        total_words=total_words,
    )


@app.route("/withdrawn")
async def withdrawn():
    return await render_template("withdrawn.html")


@app.route("/terms", methods=['GET', 'POST'])
@user_required
async def terms():
    if request.method == 'POST':
        form = await request.form
        all_checked = all(
            k in form
            for k in
            [
                "paymentacc",
                "timebox",
                "paymentdelay",
                "nostudy",
                "colldev",
                "pubdata",
                "norevoke"
            ]
        )
        if form["decision"] == "withdraw":
            user = await current_user
            user.withdraw_date = datetime.datetime.now()
            await dbsess.commit()
            del session[USER_SESSION_KEY]
            return redirect(url_for("withdrawn"))
        elif all_checked:
            user = await current_user
            user.accept_date = datetime.datetime.now()
            await dbsess.commit()
            await flash(
                "Terms accepted. "
                "You may still withdraw from the study at any point before "
                "requesting payment by replying to the invitation email."
            )
            return redirect(url_for("overview"))
        else:
            await flash("You must accept all terms to participate.")
            return redirect(url_for("terms"))
    else:
        return await render_template("terms.html")


@app.route("/proof", methods=['GET', 'POST'])
@user_required
async def proof():
    user = await current_user
    if user.proof is not None:
        await flash("Proof has already been uploaded")
        return redirect(url_for("overview"))
    if request.method == 'POST':
        form = await request.form
        user.given_name = form["givenname"]
        user.surname = form["surname"]
        files = await request.files
        fobj = files["proof"]
        plain_filename = fobj.filename
        ext = plain_filename.rsplit(".", 1)[-1].lower()
        if ext not in ["png", "jpg", "jpeg"]:
            await flash("Filename must end with .png, .jpg or .jpeg")
            return redirect(url_for("proof"))
        filename = secure_filename(user.token + "_" + plain_filename)
        os.makedirs(app.config['UPLOAD_DIR'], exist_ok=True)
        await fobj.save(pjoin(app.config['UPLOAD_DIR'], filename))
        user.proof = filename
        user.proof_upload_date = datetime.datetime.now()
        await dbsess.commit()
        await flash(
            "Proof uploaded. " +
            "It will be verified within a few days. " +
            "In the mean time you can proceed with the study."
        )
        return redirect(url_for("overview"))
    else:
        return await render_template("proof.html")


async def ajax_redirect(url):
    if request.headers.get("HX-Request"):
        redir_resp = await make_response("redir")
        redir_resp.headers["HX-Redirect"] = url
        return redir_resp
    else:
        return redirect(url)


@app.route("/selfassess", methods=['GET', 'POST'])
@user_required
async def selfassess():
    user = await current_user
    total_words = await get_total_words()
    cur_word_idx = user.next_response
    if request.method == 'POST':
        form = await request.form
        batch_complete = int(form["complete"])
        batch_target = int(form["count"])
        rating = form["rating"]
        word_id = form["word_id"]
        response_slot = (await dbsess.execute(
            select(ResponseSlot)
            .filter_by(
                word_id=word_id,
                participant_id=user.id,
            )
        )).scalars().first()
        if response_slot.response_order != cur_word_idx:
            await flash(
                "You already gave a response for that word. "
                "The new response was discarded. "
                "Please use only a single tab/window."
            )
            return await ajax_redirect(url_for("overview"))
        batch_complete += 1
        user.next_response += 1
        dbsess.add(
            Response(
                response_slot_id=response_slot.id,
                timestamp=datetime.datetime.now(),
                rating=rating,
            )
        )
        await dbsess.commit()
    else:
        batch_complete = 0
        if "count" in request.args:
            batch_target = int(request.args["count"])
        else:
            batch_target = None
    if batch_target is not None and batch_complete >= batch_target:
        await flash(
            f"Batch of {batch_target} finished."
        )
        return await ajax_redirect(url_for("overview"))
    next_word = (await dbsess.execute(
        select(Word).join(ResponseSlot).where(
            (ResponseSlot.response_order == user.next_response)
            & (ResponseSlot.participant_id == user.id)
        )
    )).scalars().first()
    if next_word is None:
        # Done
        user.selfassess_finish_date = datetime.datetime.now()
        await dbsess.commit()
        await flash(
            "Self assessment finished. "
            "Well done! Now proceed to the mini-exam."
        )
        return await ajax_redirect(url_for("overview"))
    if request.headers.get("HX-Request"):
        template = "selfassess_ajax.html"
    else:
        template = "selfassess.html"
    return await render_template(
        template,
        word=next_word.word,
        word_id=next_word.id,
        cur_word_idx=cur_word_idx + 1,
        total_words=total_words,
        batch_complete=batch_complete,
        batch_target=batch_target,
    )


@app.route('/track', methods=['POST'])
@user_required
async def track():
    form = await request.form
    event = form.get("event")
    if event == "selfassesswindowfocus":
        event_type = SessionEvent.selfassess_focus
    elif event == "selfassesswindowblur":
        event_type = SessionEvent.selfassess_unfocus
    else:
        abort(404)
    await add_event(event_type)
    return "yep"


@app.teardown_appcontext
async def teardown_db(exception):
    await dbsess.close()
