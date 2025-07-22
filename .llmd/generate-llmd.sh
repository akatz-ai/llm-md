PROJECT_REPO=$(pwd)

# Source context
llmd $PROJECT_REPO/src/llmd/ \
    -o $PROJECT_REPO/.llmd/src-context.md \
    -b "**.pyc" \
    -b "**__pycache__**"

# Tests context
llmd $PROJECT_REPO/tests/ \
    -o $PROJECT_REPO/.llmd/tests-context.md \
    -b "**.pyc" \
    -b "**__pycache__**"

# Tasks context
llmd $PROJECT_REPO/backlog/tasks/ \
    -o $PROJECT_REPO/.llmd/tasks-context.md \
    -b "**.pyc" \
    -e "**__pycache__**"