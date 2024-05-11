FROM continuumio/miniconda3
COPY . .

## SPOT INSTALLATION
RUN conda init bash && \
    . /opt/conda/etc/profile.d/conda.sh && \
    conda create --name myenv python=3.9 && \
    conda activate myenv && \
    conda install -c conda-forge spot && \
    pip install -r requirements.txt

WORKDIR /src

CMD . /opt/conda/etc/profile.d/conda.sh && conda activate myenv && python app.py

