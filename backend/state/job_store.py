import os
import pandas as pd
import config

_COLUMNS = [
    "company", "job_title", "job_nature", "email", "website",
    "details", "deadline", "posting_date", "applied", "letter",
    "job_id", "detail_url",
]


def load_jobs() -> pd.DataFrame:
    path = config.STATE_FILE
    if not os.path.exists(path):
        return pd.DataFrame(columns=_COLUMNS)
    try:
        df = pd.read_csv(path, encoding="utf-8-sig")
        for col in ("applied", "letter"):
            if col not in df.columns:
                df[col] = False
        return df
    except Exception as e:
        print(f"Warning: could not load {path}: {e}")
        return pd.DataFrame(columns=_COLUMNS)


def save_jobs(df: pd.DataFrame) -> None:
    df.to_csv(config.STATE_FILE, index=False, encoding="utf-8-sig")


def existing_keys(df: pd.DataFrame) -> set:
    return {
        (str(r.get("company", "")).strip(), str(r.get("job_title", "")).strip())
        for _, r in df.iterrows()
    }


def is_duplicate(df: pd.DataFrame, company: str, job_title: str) -> bool:
    key = (str(company).strip(), str(job_title).strip())
    return key in existing_keys(df)


def append_jobs(df: pd.DataFrame, new_rows: list[dict]) -> pd.DataFrame:
    if not new_rows:
        return df
    new_df = pd.DataFrame(new_rows)
    new_df["applied"] = new_df.apply(
        lambda r: "NO EMAIL" if not str(r.get("email", "")).strip() else False,
        axis=1,
    )
    new_df["letter"] = False
    for col in _COLUMNS:
        if col not in new_df.columns:
            new_df[col] = ""
    new_df = new_df[_COLUMNS]
    combined = pd.concat([df, new_df], ignore_index=True)
    return combined


def mark_applied(df: pd.DataFrame, idx: int) -> pd.DataFrame:
    df.loc[idx, "applied"] = True
    save_jobs(df)
    return df


def mark_letter_done(df: pd.DataFrame, idx: int) -> pd.DataFrame:
    df.loc[idx, "letter"] = True
    save_jobs(df)
    return df
