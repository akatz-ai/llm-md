PROJECT_REPO=$(pwd)

# Source context
llmd $PROJECT_REPO/src/llmd/ \
    -o $PROJECT_REPO/.llmd/src-context.md \
    -e "**.pyc" \
    -e "**__pycache__**"

# Tests context
llmd $PROJECT_REPO/tests/ \
    -o $PROJECT_REPO/.llmd/tests-context.md \
    -e "**.pyc" \
    -e "**__pycache__**"

# Tasks context
# llmd $PROJECT_REPO/backlog/tasks/ \
#     -o $PROJECT_REPO/.llmd/tasks-context.md \
#     -e "**.pyc" \
#     -e "**__pycache__**"