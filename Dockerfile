FROM cka3o4nik/jupyter3_notebook:simple

#RUN apt-get update
#RUN apt-get install 

ADD requirements.txt .
RUN pip install -r requirements.txt
RUN pip install -U PIP
#RUN pip install pymavlink==2.2.10
RUN python3 -c "import nltk; nltk.download('punkt')"

RUN apt-get clean
WORKDIR /notebooks
CMD ["jupyter", "notebook", "--ip=0.0.0.0", "--allow-root", "--NotebookApp.token='gUI0ZNdzcgJZqeGqPuGeeXRh9'"]
