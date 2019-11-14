# Serverless Transcriber on Google Cloud Platform

This serverless application will allow you to transcribe and translate your audio files using Google Cloud Platform (GCP). It uses Google Cloud Storage, Pub/Sub, Cloud Functions, Speech-to-text API and Translate API.

## Getting Started

### Prerequisites

You need to install Google Cloud SDK on your local machine OR open a cloud shell on the project in which you are going to deploy the application. You will need to enable a couple of APIs first:

```
gcloud services enable cloudfunctions.googleapis.com 
```
And repeat
```
gcloud services enable pubsub.googleapis.com
gcloud services enable speech.googleapis.com
gcloud services enable translate.googleapis.com
```

### Installing the application

You can follow the guide described in this Medium article:
[add link to article here]

## Authors

* **Aziz Ketari** - *Transcriber Application* - [PurpleBooth](https://github.com/aziz-ketari/google-cloud-apps)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Hat's off to Joe-at-LA (https://github.com/Joe-at-LA) to whom I owe the inspiration. 
