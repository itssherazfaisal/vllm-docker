import argparse
def create_vllm_dockerfile(model, tokenizor, api_format):
    dockerfile = f"""
FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu20.04
ENV DEBIAN_FRONTEND=noninteractive
ENV STAGE_DIR=/tmp
RUN mkdir -p ${{STAGE_DIR}}
RUN apt-get update && \\
    apt-get install -y python3-pip python3-dev git && \\
    rm -rf /var/lib/apt/lists/*
## install curl
RUN apt-get update && apt -y install curl
WORKDIR /code
RUN pip install --no-cache-dir --upgrade pip
## install google-cloud libs
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
RUN curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
RUN apt-get update
RUN apt-get install -y google-cloud-sdk
## install git-lfs
RUN curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash
RUN apt-get install git-lfs
## install apt-get libs
RUN apt-get install -y --no-install-recommends \\
    git \\
    wget \\
    g++ \\
    ca-certificates
## install conda
ENV PATH="/root/miniconda3/bin:${{PATH}}"
ARG PATH="/root/miniconda3/bin:${{PATH}}"
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \\
    && mkdir /root/.conda \\
    && bash Miniconda3-latest-Linux-x86_64.sh -b \\
    && rm -f Miniconda3-latest-Linux-x86_64.sh \\
    && echo "Running $(conda --version)" && \\
    rm -rf /var/lib/apt/lists/*
## create conda env
RUN conda init bash && \\
    . /root/.bashrc && \\
    conda update conda && \\
    conda create -n llm-genie && \\
    conda install python=3.9 pip && \\
    conda activate llm-genie
## install requirements
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
## copy code
COPY ./ /code
WORKDIR /code

# Clone vllm repository and install package
RUN git clone https://github.com/vllm-project/vllm.git

RUN pip install --upgrade vllm

# Install Gradio and other packages
RUN pip install --no-cache-dir --upgrade gradio

# Start vllm api server and Gradio server
# Create a startup script
RUN echo '#!/bin/bash' > /opt/startup.sh && \\
    echo 'python -u -m {'vllm.entrypoints.api_server' if api_format!='openai' else 'vllm.entrypoints.openai.api_server'} --model {model} --tokenizer {tokenizor} --host 0.0.0.0 --port 8000 2>&1 | tee api_server.log &' >> /opt/startup.sh && \\
    echo 'while ! `cat api_server.log | grep -q "Uvicorn running on"`; do sleep 1; done' >> /opt/startup.sh && \\
    echo 'python vllm/examples/gradio_webserver.py --host 0.0.0.0 --port 8001 2>&1 {"--model-url http://localhost:8000/v1/completions" if api_format=="openai" else ""} | tee gradio_server.log' >> /opt/startup.sh && \\
    chmod +x /opt/startup.sh

# Start the startup script when the container starts
CMD ["/opt/startup.sh"]
    
    """
    open("Dockerfile","w").write(dockerfile)
    return dockerfile


if __name__ == "__main__":
    # Create an argument parser
    parser = argparse.ArgumentParser(description="Script description")

    # Add arguments
    parser.add_argument("--model", type=str, default="facebook/opt-125m", help="Model Name")
    parser.add_argument("--tokenizer", type=str, default="facebook/opt-125m", help="Tokenizer")
    parser.add_argument("--api_format", type=str, default="", help="API Format")

    # Parse the arguments
    args = parser.parse_args()

    # Access the arguments
    model = args.model
    tokenizer = args.tokenizer
    api_format = args.api_format
    create_vllm_dockerfile(model, tokenizor, api_format)
  

  
