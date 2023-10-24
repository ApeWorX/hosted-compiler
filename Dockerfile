FROM apeworx/ape:latest

COPY --chown=harambe:harambe . /home/harambe/project
RUN pip install -r requirements.txt
ENV GITHUB_TOKEN=
RUN python3 vvm_versions.py
ENV PATH="/home/harambe/.local/bin:${PATH}"
ENTRYPOINT ["uvicorn", "main:app",  "--host", "0.0.0.0", "--reload"]
