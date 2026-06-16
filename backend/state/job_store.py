import os
import pandas as pd
import config

_COLUMNS = [
    "company", "job_title", "job_nature", "email", "website",
    "details", "deadline", "posting_date", "applied", "letter",
    "job_id", "detail_url", "cv_file", "letter_file",
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
        for col in ("cv_file", "letter_file"):
            if col not in df.columns:
                df[col] = ""
            else:
                df[col] = df[col].fillna("")
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
    # Cast to object first: pandas 3.x infers text columns as StringDtype, which
    # rejects a bool assignment. object dtype accepts it and saves as "True".
    df["applied"] = df["applied"].astype(object)
    df.loc[idx, "applied"] = True
    save_jobs(df)
    return df


def mark_letter_done(df: pd.DataFrame, idx: int, cv_file: str = "", letter_file: str = "") -> pd.DataFrame:
    df["letter"] = df["letter"].astype(object)
    df.loc[idx, "letter"] = True
    if cv_file:
        df.loc[idx, "cv_file"] = cv_file
    if letter_file:
        df.loc[idx, "letter_file"] = letter_file
    save_jobs(df)
    return df


def delete_job(df: pd.DataFrame, idx: int) -> pd.DataFrame:
    df = df.drop(index=idx).reset_index(drop=True)
    save_jobs(df)
    return df


def delete_all_jobs() -> None:
    save_jobs(pd.DataFrame(columns=_COLUMNS))
