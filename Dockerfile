FROM cka3o4nik/jupyter2
#FROM cka3o4nik/text_authoring:SRILM

RUN apt-get update

RUN pip2 install -U pip
#ADD SRILM /SRILM

RUN apt-get clean
WORKDIR /notebooks
CMD ["jupyter", "notebook", "--ip=0.0.0.0", "--no-browser", "--allow-root", "--NotebookApp.token='gUI0ZNdzcgJZqeGqPuGeeXRh9'"]
