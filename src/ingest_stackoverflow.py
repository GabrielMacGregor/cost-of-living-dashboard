import io
import logging
import zipfile

import pandas as pd
import requests

logger = logging.getLogger(__name__)

# Stack Overflow Developer Survey 2024 public data release.
# Update this URL when a new annual survey is published at survey.stackoverflow.co
SO_SURVEY_URL = (
    "https://cdn.stackoverflow.co/files/jo7n4k8s/production/"
    "49915bfd46d0902c3564fd9a06b509d08a20488c/"
    "stack-overflow-developer-survey-2024.zip"
)


def fetch_stackoverflow_salaries(url: str = SO_SURVEY_URL) -> pd.DataFrame:
    """Download the Stack Overflow Developer Survey and return raw salary rows.

    Returns a DataFrame with columns: Country, ConvertedCompYearly.
    Only respondents who reported a salary are included.
    """
    logger.info("Downloading Stack Overflow survey from %s", url)

    resp = requests.get(url, timeout=180, stream=True)
    resp.raise_for_status()

    content = b"".join(chunk for chunk in resp.iter_content(chunk_size=1024 * 1024))

    with zipfile.ZipFile(io.BytesIO(content)) as z:
        csv_name = next(
            (n for n in z.namelist() if "survey_results_public" in n.lower()),
            None,
        )
        if csv_name is None:
            raise RuntimeError(
                f"survey_results_public CSV not found in zip. Contents: {z.namelist()}"
            )
        logger.info("Extracting %s", csv_name)
        with z.open(csv_name) as f:
            df = pd.read_csv(f, usecols=["Country", "ConvertedCompYearly"])

    df = df.dropna(subset=["ConvertedCompYearly"])
    logger.info("Fetched %d salary rows from Stack Overflow survey", len(df))
    return df
