{{- define "bookshelf.name" -}}
{{- default "bookshelf" .Values.nameOverride -}}
{{- end -}}

{{- define "bookshelf.labels" -}}
app.kubernetes.io/name: {{ include "bookshelf.name" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end -}}
