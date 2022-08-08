FROM public.ecr.aws/lambda/python:3.9

WORKDIR /src

COPY requirements.txt /src/
RUN python -m pip install -r requirements.txt

COPY pyproject.toml poetry.lock /src/
RUN poetry config virtualenvs.create false \
 && poetry install

COPY yellows ${LAMBDA_TASK_ROOT}/yellows
