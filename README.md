## Learn aws by building simple projects

### Project Webotron
This project will help us to upload a local directory to s3 bucket and configure Route 53 and cloudfront. You can possibly use this to deploy a single page app to s3 and make it accessible to users

#### Features

   * List buckets
   * List files in a particular bucket
   * Setup bucket for deployment
   * Sync directory tree
   * Set aws profile with --profile=profile-name
   * Allow skipping files from sycing when etags match
      * `dd if=/dev/urandom of=kitten_web/bigfile.bin bs=1m count=10`
   * Now can deploy a site with CDN and SSL enabled

### Slack App for quick image resize
This is a simple slack app which will help you simplify you image resize workflow without ever leaving slack. The app is built in Serverless framework
so even got a chance to learn that framework and start using it.

Demo : https://imageresize.xyz

#### Features

   * Add menu/actions to any messages that include and image
   * /slash command for resizing to a size and url

#### AWS Features Learnt

   * AWS S3
   * Route 53 & AWS Certificate Manager
   * Cloudfront
   * AWS Lambda
   * AWS SNS
   * API Gateway


<iframe width="980" height="551" src="https://www.youtube.com/embed/G4W4SUcvrfk" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>
