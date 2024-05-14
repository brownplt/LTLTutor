# Stage 1: Build and pack the conda environment
FROM continuumio/miniconda3 AS build
COPY requirements.txt .

RUN conda init bash && \
    . /opt/conda/etc/profile.d/conda.sh && \
    conda create --name myenv python=3.9 && \
    conda activate myenv && \
    conda install -c conda-forge spot && \
    pip install -r requirements.txt 
    # && \
    #conda pack -n myenv -o /tmp/myenv.tar.gz
# Install conda-pack:
RUN conda install -c conda-forge conda-pack

# Use conda-pack to create a standalone enviornment
# in /venv:
RUN conda-pack -n myenv -o /tmp/env.tar && \
  mkdir /venv && cd /venv && tar xf /tmp/env.tar && \
  rm /tmp/env.tar

# We've put venv in same path it'll be in final image,
# so now fix up paths:
RUN /venv/bin/conda-unpack

# Stage 2: Setup the runtime
FROM debian:buster-slim
COPY . .
COPY --from=build /venv /venv

WORKDIR /src
EXPOSE 5000

# Make RUN commands use the new environment
SHELL ["/bin/bash", "-c"]

CMD /bin/bash -c "source /venv/bin/activate && python app.py"