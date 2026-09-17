{{- define "python-demo.labels" -}}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: python-demo
{{- end }}
