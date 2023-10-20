FROM apeworx/ape:latest

COPY --chown=harambe:harambe . /home/harambe/project
RUN pip install -r requirements.txt
ENV GITHUB_TOKEN=
RUN python3 vvm_versions.py
ENV PATH="/home/harambe/.local/bin:${PATH}"
ENTRYPOINT ["uvicorn", "main:app",  "--host", "0.0.0.0", "--reload"]

# COPY --chown=harambe:harambe /home/$USER/.vvm /home/harambe/.vvm
# COPY --chown=harambe:harambe .solcx /home/harambe/solcx
# DONE get vvm all versions
# NOT REQUIRED get solcx all versions
# NOT REQUIRED other languages and copy the compilers like on line 4 and 5
# TODO change print statements in vvm_versions.py to log statements
# TODO update github token environment variable with deployment token

# COPY --chown=harambe:harambe vvm_versions.py /home/harambe/project/


#DONE upload to github private under apeworx/hosted-