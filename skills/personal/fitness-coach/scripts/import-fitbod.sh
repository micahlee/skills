#!/usr/bin/env bash
set -euo pipefail

from_date="$(date -u -v-1y +%F)"
to_date="$(date -u +%F)"
output_root="/Users/micahlee/.axon/imports/fitness/fitbod"
history_limit=1200
metrics_limit=500

usage() {
  echo "usage: import-fitbod.sh [--from YYYY-MM-DD] [--to YYYY-MM-DD] [--output-root PATH]" >&2
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --from) from_date="${2:-}"; shift 2 ;;
    --to) to_date="${2:-}"; shift 2 ;;
    --output-root) output_root="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) usage; exit 2 ;;
  esac
done

for value in "$from_date" "$to_date"; do
  if ! [[ "$value" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
    echo "dates must use YYYY-MM-DD" >&2
    exit 2
  fi
done
if [ "$from_date" \> "$to_date" ]; then
  echo "--from must not be after --to" >&2
  exit 2
fi
command -v fitbod >/dev/null
command -v jq >/dev/null
command -v shasum >/dev/null

snapshot_id="$(date -u +%Y%m%dT%H%M%SZ)"
destination="${output_root}/${snapshot_id}"
if [ -e "$destination" ]; then
  echo "refusing to overwrite existing snapshot: $destination" >&2
  exit 1
fi

temporary="$(mktemp -d "${TMPDIR:-/tmp}/fitness-coach-fitbod.XXXXXX")"
cleanup() {
  case "$temporary" in
    "${TMPDIR:-/tmp}"/fitness-coach-fitbod.*) rm -rf "$temporary" ;;
  esac
}
trap cleanup EXIT

umask 077
mkdir -p "$temporary/raw/workouts" "$temporary/raw/exercises" "$temporary/raw/muscles" "$temporary/raw/templates"
printf '{"status":"in_progress","snapshot_id":"%s","from":"%s","to":"%s"}\n' \
  "$snapshot_id" "$from_date" "$to_date" > "$temporary/manifest.json"

echo "Fetching Fitbod workout index..." >&2
fitbod history list --limit "$history_limit" --json > "$temporary/raw/history-list.json"
jq --arg from "${from_date}T00:00:00Z" --arg to "${to_date}T23:59:59Z" \
  '[.workouts[] | select(.performed_at >= $from and .performed_at <= $to)]' \
  "$temporary/raw/history-list.json" > "$temporary/selected-workouts.json"

workout_total="$(jq 'length' "$temporary/selected-workouts.json")"
workout_index=0
: > "$temporary/errors.ndjson"
: > "$temporary/warnings.ndjson"
while IFS= read -r workout_id; do
  workout_index=$((workout_index + 1))
  echo "Fetching workout ${workout_index}/${workout_total}..." >&2
  if ! fitbod history show "$workout_id" --json > "$temporary/raw/workouts/${workout_id}.json"; then
    jq -cn --arg kind workout --arg id "$workout_id" '{kind:$kind,id:$id}' >> "$temporary/errors.ndjson"
  fi
done < <(jq -r '.[].workout_id' "$temporary/selected-workouts.json")

echo "Fetching Fitbod catalogs and metrics..." >&2
fitbod catalog equipment --json > "$temporary/raw/equipment.json"
fitbod catalog exercise-categories --json > "$temporary/raw/exercise-categories.json"
fitbod catalog muscle-groups --json > "$temporary/raw/muscle-groups.json"
fitbod catalog custom-exercises --json > "$temporary/raw/custom-exercises.json"
if ! fitbod metrics exercises --limit "$metrics_limit" --json > "$temporary/raw/exercise-metrics.json"; then
  jq -cn '{kind:"exercise_metrics",id:null}' >> "$temporary/errors.ndjson"
  printf '{"metrics":[]}\n' > "$temporary/raw/exercise-metrics.json"
fi

jq -s '[.[].exercises[]?.exercise_id] | unique | .[]' "$temporary"/raw/workouts/*.json \
  | jq -r . > "$temporary/exercise-ids.txt"
exercise_total="$(wc -l < "$temporary/exercise-ids.txt" | tr -d ' ')"
exercise_index=0
while IFS= read -r exercise_id; do
  [ -n "$exercise_id" ] || continue
  exercise_index=$((exercise_index + 1))
  echo "Fetching exercise ${exercise_index}/${exercise_total}..." >&2
  if ! fitbod history exercise "$exercise_id" --json > "$temporary/raw/exercises/${exercise_id}.json"; then
    jq -cn --arg kind unresolved_exercise_detail --arg id "$exercise_id" '{kind:$kind,id:$id}' >> "$temporary/warnings.ndjson"
    continue
  fi
  if ! fitbod metrics muscles "$exercise_id" --json > "$temporary/raw/muscles/${exercise_id}.json"; then
    jq -cn --arg kind unresolved_muscle_mapping --arg id "$exercise_id" '{kind:$kind,id:$id}' >> "$temporary/warnings.ndjson"
  fi
done < "$temporary/exercise-ids.txt"

echo "Fetching saved Fitbod templates..." >&2
fitbod templates list --limit 500 --json > "$temporary/raw/templates-list.json"
while IFS= read -r template_id; do
  if ! fitbod templates show "$template_id" --json > "$temporary/raw/templates/${template_id}.json"; then
    jq -cn --arg kind unresolved_template_detail --arg id "$template_id" '{kind:$kind,id:$id}' >> "$temporary/warnings.ndjson"
  fi
done < <(jq -r '.templates[].template_id' "$temporary/raw/templates-list.json")

jq -s --arg generated_at "$(date -u +%FT%TZ)" \
  '{schema_version:"fitbod_detailed_history.v1",generated_at:$generated_at,workouts:map(del(.transport,.cache))}' \
  "$temporary"/raw/workouts/*.json > "$temporary/workouts.json"
jq '{
  schema_version:"fitbod_exercised_movements.v1",
  movements:([.workouts[].exercises[] | {
    exercise_id,
    name,
    observed_equipment_ids:([.gym_equipment_id] | map(select(. != null)))
  }] | group_by(.exercise_id) | map({
    exercise_id:.[0].exercise_id,
    name:.[0].name,
    observed_equipment_ids:([.[].observed_equipment_ids[]] | unique)
  }))
}' "$temporary/workouts.json" > "$temporary/exercised-movements.json"
jq -s '{schema_version:"fitbod_exercised_catalog.v1",exercises:map(del(.transport,.cache))}' \
  "$temporary"/raw/exercises/*.json > "$temporary/exercises.json"
jq -s '{schema_version:"fitbod_exercise_muscles.v1",mappings:map(del(.transport,.cache))}' \
  "$temporary"/raw/muscles/*.json > "$temporary/exercise-muscles.json"
jq -s '{schema_version:"fitbod_templates.v1",templates:map(del(.transport,.cache))}' \
  "$temporary"/raw/templates/*.json > "$temporary/templates.json"

error_count="$(wc -l < "$temporary/errors.ndjson" | tr -d ' ')"
warning_count="$(wc -l < "$temporary/warnings.ndjson" | tr -d ' ')"
jq -n \
  --arg snapshot_id "$snapshot_id" \
  --arg created_at "$(date -u +%FT%TZ)" \
  --arg from "$from_date" \
  --arg to "$to_date" \
  --argjson history_row_count "$workout_total" \
  --argjson workout_count "$(jq '.workouts|length' "$temporary/workouts.json")" \
  --argjson movement_count "$(jq '.movements|length' "$temporary/exercised-movements.json")" \
  --argjson exercise_count "$(jq '.exercises|length' "$temporary/exercises.json")" \
  --argjson metric_count "$(jq '.metrics|length' "$temporary/raw/exercise-metrics.json")" \
  --argjson custom_exercise_count "$(jq '.items|length' "$temporary/raw/custom-exercises.json")" \
  --argjson equipment_count "$(jq '.items|length' "$temporary/raw/equipment.json")" \
  --argjson category_count "$(jq '.items|length' "$temporary/raw/exercise-categories.json")" \
  --argjson muscle_group_count "$(jq '.items|length' "$temporary/raw/muscle-groups.json")" \
  --argjson template_count "$(jq '.templates|length' "$temporary/templates.json")" \
  --argjson set_count "$(jq '[.workouts[].exercises[].sets[]] | length' "$temporary/workouts.json")" \
  --argjson completed_set_count "$(jq '[.workouts[].exercises[].sets[] | select(.completed)] | length' "$temporary/workouts.json")" \
  --argjson error_count "$error_count" \
  --argjson warning_count "$warning_count" \
  '{
    status:(if $error_count == 0 then "complete" else "complete_with_errors" end),
    schema_version:"fitness_coach_fitbod_seed.v1",
    snapshot_id:$snapshot_id,
    created_at:$created_at,
    date_range:{from:$from,to:$to},
    counts:{
      history_rows_selected:$history_row_count,
      duplicate_history_rows:($history_row_count-$workout_count),
      workouts:$workout_count,
      exercised_movements:$movement_count,
      resolved_exercise_details:$exercise_count,
      metric_bearing_exercises:$metric_count,
      custom_exercises:$custom_exercise_count,
      equipment:$equipment_count,
      exercise_categories:$category_count,
      muscle_groups:$muscle_group_count,
      templates:$template_count,
      sets:$set_count,
      completed_sets:$completed_set_count,
      errors:$error_count,
      warnings:$warning_count
    },
    catalog_scope:"all exercised movements in selected history (including names retained when old detail endpoints return 404), all custom exercises, up to 500 metric-bearing exercises, equipment, exercise categories, and muscle groups",
    limitations:["The current Fitbod CLI does not expose the full global standard-exercise catalog as one export."],
    contains_personal_data:true
  }' > "$temporary/manifest.json"

(
  cd "$temporary"
  find . -type f ! -name checksums.txt -print | LC_ALL=C sort | while IFS= read -r file; do
    shasum -a 256 "$file"
  done
) > "$temporary/checksums.txt"

mkdir -p "$output_root"
chmod 700 "$output_root"
mv "$temporary" "$destination"
trap - EXIT
chmod -R go-rwx "$destination"
echo "$destination"
