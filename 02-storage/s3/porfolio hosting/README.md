# AWS S3 Static Portfolio Hosting

## Project overview

This experiment deploys a personal portfolio website with Amazon S3 Static Website Hosting. The site files are stored at the bucket root and served through the public S3 website endpoint.

**Live website:** [Open the deployed portfolio](http://gokul-portfolio-2026.s3-website.eu-north-1.amazonaws.com/)

## AWS configuration

| Configuration | Value |
| --- | --- |
| AWS service | Amazon S3 |
| Bucket | `gokul-portfolio-2026` |
| Region | `eu-north-1` (Stockholm) |
| Hosting | Static Website Hosting |
| Index document | `index.html` |
| Error document | `index.html` |

## Architecture

```text
Local portfolio files
        ↓
AWS CLI authentication
        ↓
Amazon S3 bucket
        ↓
S3 Static Website Hosting
        ↓
Public website endpoint
```

## Implementation

1. Created the S3 bucket in `eu-north-1`.
2. Uploaded the portfolio files to the bucket root.
3. Enabled static website hosting.
4. Configured `index.html` as the index and error document.
5. Enabled public website access for the hosted objects.
6. Verified the public endpoint.

## Troubleshooting

The site initially returned `404 NoSuchKey` because `index.html` was inside a nested folder. Moving the website files to the bucket root resolved the error.

```text
gokul-portfolio-2026/
├── index.html
├── styles.css
├── main.js
├── 404.html
├── robots.txt
└── sitemap.xml
```

## Source files

The [`website/`](website/) folder contains the deployed HTML, CSS, JavaScript, `robots.txt`, and sitemap. Personal résumé PDFs and the profile image remain in the deployed S3 bucket and are intentionally excluded from this repository copy.

## Learning outcomes

- Configure Amazon S3 static website hosting.
- Organize website objects at the bucket root.
- Configure public access for hosted objects.
- Diagnose S3 `404 NoSuchKey` errors.
- Maintain an AWS experiment in GitHub.

## Future improvements

- Add Amazon CloudFront for HTTPS and caching.
- Connect a custom domain.
- Automate deployment with GitHub Actions.

## Author

Gokul M · [GitHub](https://github.com/GOKUL5731)
