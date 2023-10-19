FROM apeworx/ape:latest

COPY --chown=harambe:harambe . /home/harambe/project
RUN pip install -r requirements.txt
RUN python3 vvm_versions.py

# COPY --chown=harambe:harambe /home/$USER/.vvm /home/harambe/.vvm
# COPY --chown=harambe:harambe .solcx /home/harambe/solcx
# TODO get vvm all versions
# TODO get solcx all versions
# TODO other languages and copy the compilers like on line 4 and 5

# COPY --chown=harambe:harambe vvm_versions.py /home/harambe/project/
# RUN python3 vvm_versions.py


#TODO upload to github private under ape/remix