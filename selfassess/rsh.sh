#!/bin/bash
set -o xtrace;
set -euo pipefail;

POD=$(oc get pods --field-selector=status.phase=Running --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}')
exec oc rsh $POD
