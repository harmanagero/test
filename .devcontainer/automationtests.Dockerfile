#Pull postman/newman image from docker hub
FROM postman/newman

# Install Junit Reporter. You will only be able to get all the iterations to report by using newman-reporter-junitfull
# you don't need this if you dont have only 1 iteration to run.
RUN npm install -g newman-reporter-junitfull

WORKDIR /etc/newman

ENTRYPOINT ["newman"]
