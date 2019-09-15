project := 'whodatbot'

_list:
  @just --list

run +args='':
  python -m {{project}} {{args}}
