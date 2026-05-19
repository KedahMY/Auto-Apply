import pandas as pd
import sys
import os
import time

# Try to import win32com for Outlook automation
try:
    import win32com.client
    OUTLOOK_AVAILABLE = True
except ImportError:
    OUTLOOK_AVAILABLE = False

def send_single_email(df, job_idx):
    """Send email for a single job"""
    job = df.iloc[job_idx]
    company = job.get('company', 'Unknown Company')
    job_title = job.get('job_title', 'Unknown Position')
    email = job.get('email', '')
    
    print(f"\nProcessing Job (Row {job_idx + 1}):")
    print(f"Company: {company}")
    print(f"Position: {job_title}")
    print(f"Email: {email}")
    
    if not email or pd.isna(email):
        print("Error: No email address found - skipping")
        return False
    
    # Check if cover letter exists before proceeding
    # Use same filename sanitization as coverletter.py
    safe_filename = f"{company} {job_title}".replace('/', '_').replace('\\\\', '_').replace(':', '_').replace('?', '_').replace('*', '_').replace('|', '_').replace('<', '_').replace('>', '_').replace('"', '_')
    cover_letter_path = os.path.join(os.getcwd(), "CoverLetter", f"{safe_filename}.pdf")
    if not os.path.exists(cover_letter_path):
        print(f"Error: Cover letter not found at {cover_letter_path} - skipping")
        return False
    
    try:
        print("Preparing email...")
        outlook = win32com.client.Dispatch('outlook.application')
        mail = outlook.CreateItem(0)
        
        # Set email properties
        mail.To = email
        mail.Subject = f"Application for {job_title}"
        mail.BCC = "tzkhoo@connect.ust.hk"
        mail.BodyFormat = 1  # Plain text
        
        # Email body
        email_text = f"""Dear {company},

I am interested to apply for the internship opportunity offered for the {job_title} role. 

As a final-year Computer Engineering student at HKUST, I thrive on initiating projects and applying knowledge to real-world problems. Something unique about me is my ability to bridge engineering with business strategy. I have a strong passion for tackling business case competitions as well as hackathons, and have won 11 podium awards.

Attached is my CV and cover letter as requested, I hope I can combine my technical execution with strategic insight to deliver results for your company.

Best Regards,
Thien Zhi"""
        
        mail.Body = email_text
        
        # Add CV attachment
        cv_path = os.path.join(os.getcwd(), "Thien Zhi CV.pdf")
        if os.path.exists(cv_path):
            mail.Attachments.Add(cv_path)
            print("Attached: CV")
        else:
            print("Warning: CV not found")
        
        # Add cover letter attachment (already verified it exists)
        mail.Attachments.Add(cover_letter_path)
        print("Attached: Cover Letter")
        
        # Send the email
        mail.Send()
        print("Email sent successfully!")
        return True
        
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def main():
    """Main function - send multiple emails with batch processing"""
    print("HKUST Job Application Email Sender")
    print("=" * 40)
    
    # Load CSV file
    try:
        df = pd.read_csv('hkust_job.csv', encoding='utf-8-sig')
        print(f"Loaded {len(df)} jobs from CSV")
    except FileNotFoundError:
        print("Error: hkust_job.csv file not found!")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading CSV: {e}")
        sys.exit(1)
    
    # Check Outlook availability
    if not OUTLOOK_AVAILABLE:
        print("Error: Outlook not available! Install: pip install pywin32")
        return
    
    # Check if 'applied' column exists
    if 'applied' not in df.columns:
        df['applied'] = 'False'
        df.to_csv('hkust_job.csv', index=False, encoding='utf-8-sig')
        print("Created 'applied' column - all jobs marked as not applied")
    
    # Find unapplied jobs (handle both boolean False and string 'False')
    unapplied_jobs = df[
        (df['applied'] == 'False') | 
        (df['applied'] == False) | 
        (df['applied'].astype(str).str.lower() == 'false')
    ]
    if unapplied_jobs.empty:
        print("All jobs with email addresses have been applied to!")
        return
    
    # Show status summary
    applied_count = (
        (df['applied'] == 'True') | 
        (df['applied'] == True) |
        (df['applied'].astype(str).str.lower() == 'true')
    ).sum()
    no_email_count = (df['applied'] == 'NO EMAIL').sum()
    unapplied_count = len(unapplied_jobs)
    
    print(f"Status summary:")
    print(f"  Applied: {applied_count}")
    print(f"  No email: {no_email_count}")
    print(f"  Ready to apply: {unapplied_count}")
    
    print(f"Found {len(unapplied_jobs)} jobs ready for application")
    
    # Get first unapplied job info for preview
    first_job_idx = unapplied_jobs.index[0]
    first_job = df.iloc[first_job_idx]
    print(f"\nNext jobs starting from Row {first_job_idx + 1}:")
    print(f"Company: {first_job.get('company', 'Unknown Company')}")
    print(f"Position: {first_job.get('job_title', 'Unknown Position')}")
    
    # Ask for number of emails to send
    try:
        num_emails = int(input(f"\nHow many emails do you want to send? (1-{len(unapplied_jobs)}): ").strip())
        if num_emails < 1 or num_emails > len(unapplied_jobs):
            print("Invalid number. Cancelled.")
            return
    except ValueError:
        print("Invalid input. Cancelled.")
        return
    
    # Preview which jobs will be processed and check email + cover letters
    print(f"\n--- PREVIEW: Next {num_emails} job(s) ---")
    jobs_ready_to_send = 0
    for i in range(min(num_emails, len(unapplied_jobs))):
        job_idx = unapplied_jobs.index[i]
        job = df.iloc[job_idx]
        company = job.get('company', 'Unknown Company')
        job_title = job.get('job_title', 'Unknown Position')
        email = job.get('email', '')
        
        # Check if email exists
        has_email = email and not pd.isna(email) and str(email).strip() != ''
        
        # Check if cover letter exists
        safe_filename = f"{company} {job_title}".replace('/', '_').replace('\\\\', '_').replace(':', '_').replace('?', '_').replace('*', '_').replace('|', '_').replace('<', '_').replace('>', '_').replace('"', '_')
        cover_letter_path = os.path.join(os.getcwd(), "CoverLetter", f"{safe_filename}.pdf")
        has_cover_letter = os.path.exists(cover_letter_path)
        
        # Determine status
        if has_email and has_cover_letter:
            status = "✓"
            jobs_ready_to_send += 1
        elif not has_email and not has_cover_letter:
            status = "✗ (no email & no cover letter)"
        elif not has_email:
            status = "✗ (no email)"
        else:  # not has_cover_letter
            status = "✗ (no cover letter)"
            
        print(f"{i+1}. Row {job_idx + 1}: {company} - {job_title} {status}")
    
    if jobs_ready_to_send == 0:
        print("\nNo jobs have both email addresses and cover letters available. Cannot send any emails.")
        return
    
    print(f"\n{jobs_ready_to_send} out of {num_emails} jobs are ready to send.")
    print(f"Jobs without email addresses or cover letters will be skipped.")
    print(f"Emails will be sent with 5 second cooldown between successful emails (skipped jobs have no delay)")

    
    confirm = input("Proceed? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("Cancelled")
        return
    
    # Send emails in batch
    successful_sends = 0
    failed_sends = 0
    skipped_jobs = 0
    
    for i in range(num_emails):
        job_idx = unapplied_jobs.index[i]
        
        print(f"\n--- Email {i+1}/{num_emails} ---")
        
        # Check current job for email and cover letter BEFORE attempting to send
        job = df.iloc[job_idx]
        company = job.get('company', 'Unknown Company')
        job_title = job.get('job_title', 'Unknown Position')
        email = job.get('email', '')
        
        # Check if email exists for current row
        has_email = email and not pd.isna(email) and str(email).strip() != ''
        
        # Check if cover letter exists for current row
        safe_filename = f"{company} {job_title}".replace('/', '_').replace('\\\\', '_').replace(':', '_').replace('?', '_').replace('*', '_').replace('|', '_').replace('<', '_').replace('>', '_').replace('"', '_')
        cover_letter_path = os.path.join(os.getcwd(), "CoverLetter", f"{safe_filename}.pdf")
        has_cover_letter = os.path.exists(cover_letter_path)
        
        # If missing email or cover letter, mark as "NO EMAIL" and skip (no delay)
        if not has_email:
            print(f"Skipping Row {job_idx + 1}: {company} - {job_title} (no email address)")
            df.loc[job_idx, 'applied'] = 'NO EMAIL'
            skipped_jobs += 1
            # Save CSV update immediately
            try:
                df.to_csv('hkust_job.csv', index=False, encoding='utf-8-sig')
            except Exception as e:
                print(f"Warning: Could not update CSV: {e}")
            continue  # Skip to next job immediately (no delay)
        
        if not has_cover_letter:
            print(f"Skipping Row {job_idx + 1}: {company} - {job_title} (cover letter not found)")
            # Keep as 'False' so user can generate cover letter and try again later
            skipped_jobs += 1
            continue  # Skip to next job immediately (no delay)
        
        # Send the email (only if both email and cover letter exist)
        success = send_single_email(df, job_idx)
        
        if success:
            # Mark as applied in CSV
            try:
                df.loc[job_idx, 'applied'] = 'True'
                df.to_csv('hkust_job.csv', index=False, encoding='utf-8-sig')
                print("Job marked as applied")
                successful_sends += 1
            except Exception as e:
                print(f"Warning: Could not update CSV: {e}")
                successful_sends += 1  # Email was sent even if CSV update failed
            
            # Add cooldown after successful send (except for the last email)
            if i < num_emails - 1:
                print("Waiting 5 seconds before next email...")
                time.sleep(5)
        else:
            # Email send failed (not skipped due to missing requirements)
            failed_sends += 1
    
    # Summary
    print(f"\n=== BATCH COMPLETE ===")
    print(f"Successfully sent: {successful_sends}")
    print(f"Skipped (missing email/cover letter): {skipped_jobs}")
    print(f"Failed to send: {failed_sends}")
    print(f"Total processed: {successful_sends + failed_sends + skipped_jobs}")

if __name__ == "__main__":
    main()