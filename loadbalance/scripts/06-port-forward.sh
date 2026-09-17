#!/usr/bin/env bash
set -euo pipefail
cat <<'MSG'
Open two terminals:

Terminal 1:
  kubectl -n python-demo port-forward svc/python-web 8080:80
  Then open: http://localhost:8080

Terminal 2:
  kubectl -n python-demo port-forward svc/python-api 8081:80
  Then run:
  curl 'http://localhost:8081/api/hello?name=Zach'
MSG
