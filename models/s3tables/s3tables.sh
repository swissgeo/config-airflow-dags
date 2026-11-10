#!/bin/bash
set -uo pipefail

operation="${1:-}"

if [[ -z "$operation" ]]; then
  echo "Usage: $0 <upgrade|check> [dir]" >&2
  exit 2
fi


_tmp_file () {
  # Create a temporary file and substitute the variables in the JSON
  # with env variables
  local file="$1"
  local tmp_file
  tmp_file="$(mktemp)"
  cat "$file" | envsubst >> "$tmp_file"
  echo "$tmp_file"
}

_table_exists() {
  local tmp_file="$1"

  # Extracting the values for the list command from the JSON file
  local TABLE_BUCKET_ARN NAMESPACE TABLE_NAME
  TABLE_BUCKET_ARN=$(jq -er '.tableBucketARN' "$tmp_file")
  NAMESPACE=$(jq -er '.namespace' "$tmp_file")
  TABLE_NAME=$(jq -er '.name' "$tmp_file")

  aws s3tables list-tables \
    --table-bucket-arn "$TABLE_BUCKET_ARN" \
    --namespace "$NAMESPACE" \
    --profile "$AWS_PROFILE" \
    --region "$AWS_REGION" \
    --query "length(tables[?name=='${TABLE_NAME}'])" \
    --output json
}

upgrade() {
  local file="$1"
  [[ -f "$file" ]] || return 1

  echo "Upgrading: $file"

  local tmp_file
  tmp_file="$(_tmp_file "$file")"

  # Testing if the table already exists
  local count
  count=$(_table_exists "$tmp_file") || return "$?"

  if (( count > 0 )); then
    # do nothing
    echo "Table already exists: $file"

    rm "${tmp_file}" 2>/dev/null

    return
  fi

  aws s3tables create-table --profile "${AWS_PROFILE}" --region "${AWS_REGION}" --cli-input-json "file://${tmp_file}"

  rm "${tmp_file}" 2>/dev/null
}

check() {
  local file="$1"
  [[ -f "$file" ]] || return 1

  local tmp_file
  tmp_file="$(_tmp_file "$file")"

  local count
  count=$(_table_exists "$tmp_file") || return "$?"

  if (( count > 0 )); then
    printf '\033[32mTable exists: %s\033[0m\n' "$file"
  else
    printf '\033[31mTable does not exist: %s\033[0m\n' "$file"
  fi

  rm "${tmp_file}" 2>/dev/null
}

process() {
  local file="$1"
  [[ -f "$file" ]] || return 1   # ensure it exists and is a file
  case "$operation" in
    upgrade) upgrade "$file" ;;
    check)   check   "$file" ;;
    *)       echo "Unknown mode: $operation" >&2; return 2 ;;
  esac
}

find models -type f -name '*.json' -print0 |
while IFS= read -r -d '' f; do
  process "$f"
done
