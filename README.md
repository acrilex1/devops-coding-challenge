# Coveo DevOps Challenge

## The challenge

One of your colleagues has started a project to analyze the files from an S3 bucket, output some information about them,
and calculate the cost of the storage. The project is not finished and he had to leave for personal reasons.
Your manager is asking you to finish the project and make it production-ready.

## Specifications

The tool is a shell command line utility that returns information over all [S3](https://aws.amazon.com/documentation/s3/) buckets in an Amazon account.

- The tool must work on Linux, OSX and Windows.
- It must be easy to install and use.
- Ideally, the tool won't require installation of any other tools / libraries / frameworks to work.
- Time is money, we cannot afford running a tool that takes hours to complete, your solution should return results within seconds (or minutes if you are willing to test our patience :-).

### The tool must return the following information

For each bucket:
- Name
- Creation date
- Number of files
- Total size of files
- Last modified date of the most recent file
- And the most important of all, **how much does it cost**

Your colleague has started the task and was well on his way to achieve the above with the code you will find in this branch.
**Although the code already runs, there are some TODO's left in the code for you to complete.**

## To prepare for your interview:

- Make sure you can run the code and understand what's going on in the code.
- Review the code and take notes on stuff you would improve or change. Assume this code is about to be in production
and that you have to plan the next few releases. Having an agile process in mind, what would you change in the first release, second
release, etc. This will help us focus our discussion on what's important first.
- Make sure you have addressed all the TODO's that were left in the code.
- Make sure to have a setup that allows you to hit a breakpoint and debug in a step-by-step manner. It doesn't matter which
application you use to do it, but make sure you're comfortable debugging in the environment you choose before the interview,
because bugs there will be 😉.
- Have an editor or IDE ready to code during the interview.
- Have Git installed.

Your colleague who started this didn't follow our normal standards, so you should have something to say about that code.
If you want to go the extra mile, you can improve on his work ahead of the interview, but being able to comment on what
you think is wrong and why you think it could be improved is more important than actually fixing any of it.
We are not looking for a perfect solution, we are more interested in your thought process and how you would approach
the problem.

We expect you to understand the whole project a minimum and have an opinion on it. We understand that you may not be 100%
familiar with AWS. It's normal and we don't expect you to learn everything before the interview.

## Running it

1. First you'll need to create an AWS account. One can be created for free.
2. Create an S3 bucket and upload some files into it. Bear in mind that there can be a charge if you go over the
[free tier requirements](https://aws.amazon.com/free/?all-free-tier.sort-by=item.additionalFields.SortRank&all-free-tier.sort-order=asc&awsf.Free%20Tier%20Types=*all&awsf.Free%20Tier%20Categories=*all&all-free-tier.q=S3&all-free-tier.q_operator=AND)
(5 GiB at time of writing).
3. To run the project itself, you'll need Python 3.8 or more recent and [Poetry](https://python-poetry.org/docs/#installation)
4. Run `poetry install`
5. Run `poetry run python ./main.py`

## During the technical interview

Be prepared for a peer review during your technical interview. Also expect some additional challenges as we may ask you
to run your program in a different environment with a significant number of files.

## Final advice

Make sure you have fun while performing this challenge. It is very rare that candidates grasp the extent of the pitfalls to
avoid and all the technical challenges involved. We are not looking for perfection, but you will be evaluated on your ability
to adapt when we face the various problems that you will inevitably be confronted.

During the interview, treat the interviewers as colleagues. Feel free to ask for help as you would normally do in the course
of your job. They are there to help you, not to trick you. Their main objective is to find in you their future colleague with
whom they will enjoy working.

See you soon.

## Notice on Generative AI Use (GitHub Copilot)

GitHub Copilot was used as part of the process of completing this assessment. Regardless, extensive research and manual review were conducted to achieve an optimal result and to respect the scope of work. In today's software development landscape, a good engineer's skills now include being able to properly use Large Language Models (LLMs) in agent mode. GitHub Copilot and similar AI tools have become essential productivity multipliers that enable developers to focus on higher-level architecture, problem-solving, and code quality while automating repetitive tasks and providing intelligent code suggestions.

## Usage Instructions

### Running the Script (from repo root)

```bash
# Analyze all buckets
poetry run python -m src.main

# Analyze specific bucket
poetry run python -m src.main my-bucket-name

# JSON output format
poetry run python -m src.main my-bucket-name --json

# Using Docker Compose (LocalStack)
docker compose up -d
poetry run python -m src.main
docker compose down
```

## New Features and Improvements

This enhanced version includes the following improvements:

### Docker Compose with LocalStack

For local development and testing without AWS costs:

1. Copy the environment template: `cp .env.template .env`
2. Start LocalStack: `docker compose up -d`
3. Run the script: `poetry run python -m src.main`
4. Stop LocalStack: `docker compose down`

### Enhanced Features

- **Async Operations**: Uses aioboto3 for improved performance with large numbers of buckets
- **Proper Pagination**: Handles buckets with millions of objects efficiently
- **Cost Calculation**: 
  - Real-time pricing from AWS Pricing API
  - Estimated monthly costs based on current storage
- **Rate Limiting**: Adaptive retry mode with configurable max attempts
- **Error Handling**: Graceful handling of various AWS error scenarios
- **Comprehensive Testing**: Unit tests and e2e tests

### Future improvements/limitations
- Real-world costs could be evaluated with Cost Explorer, which would be cheaper and more reliable than object enumeration, including parameters such as API calls costs.
- This assumes list prices, does not account for Private Pricing Agreements

### Cost and Performance Considerations

**API Costs Per Operation:**
- List buckets: ~$0.005 per 1,000 bucket operations
- List objects: ~$0.0004 per 1,000 requests
- Pricing API: Free tier available

**Example Costs:**
- 1M objects across 10 buckets: ~$400 in LIST operations
- 1,000 buckets in account: ~$5 in bucket listing

**Performance:**
- Small buckets (<1K objects): Seconds
- Large buckets (>1M objects): Minutes
- Multiple large buckets: Can take hours
- Uses recursive prefix listing with configurable depth for optimal performance on hierarchical structures

⚠️ **WARNING**: Running against all buckets in an account with many large buckets can incur significant API costs. Always test with specific buckets first.

### Environment Configuration

Configure AWS credentials and settings in `.env`:

```bash
# Copy template and edit
cp .env.template .env
# Edit .env with your AWS credentials
```

#### Configuration Variables

- `MAX_CONCURRENT_BUCKETS`: Limits concurrent bucket processing (optional, no limit by default)
- `MAX_RECURSION_DEPTH`: Controls recursive prefix listing depth (default: 4)
  - Higher values improve efficiency for deeply nested folder structures
  - Lower values reduce memory usage and prevent stack overflow for extremely deep structures
  - At max depth, switches to flat listing without prefixes
- `S3_PREFIX_DELIMITER`: Character used as directory separator in S3 object keys (default: "/")
  - Common alternatives: "-", "_", "|" for different naming conventions

### Testing

```bash
# Install dependencies
poetry install

# Run unit tests
poetry run pytest tests/unit/ -v --cov

# Run e2e tests (requires LocalStack or AWS)
docker compose up -d  # For LocalStack
poetry run pytest tests/e2e/ -v

# Run all tests
poetry run pytest -v
```

### Debugging E2E Tests

For debugging E2E tests, you can use Python's `debugpy` debugger by setting the `E2E_DEBUG=1` environment variable:

```bash
# Run E2E tests with debugpy debugger
E2E_DEBUG=1 poetry run pytest tests/e2e/test_e2e.py::TestE2ECliOutput::test_cli_with_specific_bucket -s

# Debug specific test case
E2E_DEBUG=1 poetry run pytest tests/e2e/test_e2e.py::TestE2ECliOutput::test_cli_with_nonexistent_bucket -s
```

When `E2E_DEBUG=1` is set, the CLI will run under `python -m debugpy`.

### Required AWS IAM Permissions

For full functionality, the AWS credentials need these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListAllMyBuckets",
        "s3:ListBucket",
        "s3:GetBucketLocation"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "pricing:GetProducts"
      ],
      "Resource": "*"
    }
  ]
}
```

Note: If a single bucket has to be listed, permissions can be narrowed down accordingly.

## GitHub Actions

Two workflows are included:

1. **Tests**: Runs on push/PR with LocalStack
2. **Run against real S3**: Manual workflow for testing against real AWS (requires secrets setup)

## Security Tooling

This repository uses GitHub Advanced Security features:
- **CodeQL**: Automated security scanning
- **Dependabot**: Dependency vulnerability monitoring  
- **Secret Scanning**: Prevents credential exposure

These tools demonstrate modern DevSecOps practices for secure software development.
