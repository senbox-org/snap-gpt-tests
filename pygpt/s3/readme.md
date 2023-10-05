# Reports on s3

## Deploy to s3

1. First copy/paste `index.html` and `error.html` to `static` folder
2. Upload all files with correct permissions `aws s3 sync ../statics s3://snap-reports/ --endpoint-url https://s3.sbg.io.cloud.ovh.net --region sbg --acl public-read`
3. Update bucket `aws s3 website s3://snap-reports/ --endpoint-url https://s3.sbg.io.cloud.ovh.net --region sbg --index-document index.html --error-document error.html`

## Update pipelines

Now pipelines should be configured to upload reports to

* `<bucket_name>/linux`
* `<bucket_name>/windows`
* `<bucket_name>/macos`