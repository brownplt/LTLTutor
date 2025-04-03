# Stage 1: Build and pack the conda environment
FROM continuumio/miniconda3 AS build

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN conda init bash && \
    . /opt/conda/etc/profile.d/conda.sh && \
    conda create --name myenv python=3.9 && \
    conda activate myenv && \
    conda install -c conda-forge spot && \
    pip install -r requirements.txt

# Install conda-pack
RUN conda install -c conda-forge conda-pack

# Use conda-pack to create a standalone environment in /venv
RUN conda-pack -n myenv -o /tmp/env.tar && \
    mkdir /venv && cd /venv && tar xf /tmp/env.tar && \
    rm /tmp/env.tar

# Fix paths for the standalone environment
RUN /venv/bin/conda-unpack

# Install Java (required for ANTLR)
RUN apt-get update && apt-get install -y default-jre curl

# Download ANTLR
RUN curl -O https://www.antlr.org/download/antlr-4.13.0-complete.jar

# Copy the grammar file
COPY src/ltl.g4 /src/

# Generate the ANTLR parser and lexer files
WORKDIR /src
RUN java -jar /antlr-4.13.0-complete.jar -Dlanguage=Python3 ltl.g4

# Stage 2: Setup the runtime
FROM debian:buster-slim

# Copy the application code and the standalone environment
COPY . .
COPY --from=build /venv /venv

# Set the working directory
WORKDIR /src

# Expose the application port
EXPOSE 5000

# Make RUN commands use the new environment
SHELL ["/bin/bash", "-c"]

# Command to run the application
CMD /bin/bash -c "source /venv/bin/activate && python app.py"