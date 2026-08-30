import os
import zipfile
import tarfile
import gzip
import shutil
import sys

def count_pi_files(root_dir):
    """Count all SDD2 .pi files discoverable under root_dir."""
    pi_count = 0
    for root, dirs, files in os.walk(root_dir):
        for f in files:
            if 'SDD2' in f and f.endswith('.pi'):
                pi_count += 1
    return pi_count

def get_target_path_for_archive(archive_path):
    """
    Determine target folder/file path by stripping known archive extensions.
    """
    filename = os.path.basename(archive_path)
    parent_dir = os.path.dirname(archive_path)
    
    known_exts = ['.tar.gz', '.tgz', '.zip', '.tar', '.gz']
    matched_ext = None
    for ext in known_exts:
        if filename.lower().endswith(ext):
            matched_ext = ext
            break
            
    if not matched_ext:
        return None, None
        
    base_name = filename[:-len(matched_ext)]
    target_path = os.path.join(parent_dir, base_name)
    return target_path, matched_ext

def is_already_extracted(archive_path, target_path, ext):
    """
    Check if the archive has already been extracted into target_path with non-empty content.
    """
    if ext in ['.zip', '.tar', '.tar.gz', '.tgz']:
        if os.path.exists(target_path) and os.path.isdir(target_path):
            # Check if directory contains non-empty content
            contents = os.listdir(target_path)
            if len(contents) > 0:
                return True
        return False
    elif ext == '.gz':
        # For .gz (e.g. AL1_SOLEXS_20260704_SDD2_L1.pi.gz)
        # target_path might be a folder containing AL1_SOLEXS_20260704_SDD2_L1.pi
        # or target_path might be a single file AL1_SOLEXS_20260704_SDD2_L1.pi
        if os.path.isdir(target_path):
            inner_file = os.path.join(target_path, os.path.basename(target_path))
            if os.path.exists(inner_file) and os.path.getsize(inner_file) > 0:
                return True
            if len(os.listdir(target_path)) > 0:
                return True
        elif os.path.isfile(target_path) and os.path.getsize(target_path) > 0:
            return True
        return False
    return False

def extract_archive(archive_path, target_path, ext):
    """Extract a single archive."""
    try:
        if ext == '.zip':
            with zipfile.ZipFile(archive_path, 'r') as zf:
                zf.extractall(os.path.dirname(archive_path))
            return True, "Success"
        elif ext in ['.tar', '.tar.gz', '.tgz']:
            mode = 'r:*' if ext != '.tar' else 'r'
            with tarfile.open(archive_path, mode) as tf:
                tf.extractall(os.path.dirname(archive_path))
            return True, "Success"
        elif ext == '.gz':
            # Create target folder if it doesn't exist
            if not os.path.exists(target_path):
                os.makedirs(target_path, exist_ok=True)
            output_file = os.path.join(target_path, os.path.basename(target_path))
            with gzip.open(archive_path, 'rb') as f_in:
                with open(output_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            return True, "Success"
        else:
            return False, f"Unsupported extension: {ext}"
    except Exception as e:
        return False, str(e)

def run_extraction_pipeline(root_dir):
    print("=" * 60)
    print("STEP 1: RECURSIVE ARCHIVE EXTRACTION")
    print("=" * 60)
    
    before_count = count_pi_files(root_dir)
    print(f"Discoverable SDD2 .pi files BEFORE extraction: {before_count}")
    
    pass_number = 1
    total_extracted = 0
    failed_archives = []
    
    while True:
        print(f"\n--- Starting Extraction Pass {pass_number} ---")
        extracted_this_pass = 0
        archives_found = []
        
        for root, dirs, files in os.walk(root_dir):
            for f in files:
                filepath = os.path.join(root, f)
                target_path, ext = get_target_path_for_archive(filepath)
                if ext is not None:
                    archives_found.append((filepath, target_path, ext))
                    
        print(f"Found {len(archives_found)} archive candidates in pass {pass_number}.")
        
        skipped_count = 0
        for archive_path, target_path, ext in archives_found:
            if is_already_extracted(archive_path, target_path, ext):
                skipped_count += 1
                continue
                
            print(f"Extracting: {os.path.basename(archive_path)} -> {os.path.basename(target_path)} ...")
            success, msg = extract_archive(archive_path, target_path, ext)
            if success:
                extracted_this_pass += 1
                total_extracted += 1
            else:
                print(f"  FAILED: {os.path.basename(archive_path)} | Error: {msg}")
                failed_archives.append((archive_path, msg))
                
        print(f"Pass {pass_number} summary: {extracted_this_pass} extracted, {skipped_count} skipped (already extracted).")
        
        if extracted_this_pass == 0:
            print("\nNo new archives extracted in this pass. Extraction complete!")
            break
            
        pass_number += 1
        if pass_number > 10:  # Safety cap against infinite loops
            print("\nReached maximum pass limit (10 passes). Stopping extraction.")
            break
            
    after_count = count_pi_files(root_dir)
    print("\n" + "=" * 60)
    print(f"EXTRACTION COMPLETE")
    print(f"Total passes executed: {pass_number}")
    print(f"Total archives extracted: {total_extracted}")
    print(f"Discoverable SDD2 .pi files BEFORE: {before_count}")
    print(f"Discoverable SDD2 .pi files AFTER:  {after_count}")
    if failed_archives:
        print(f"Failed archives ({len(failed_archives)}):")
        for fa, reason in failed_archives:
            print(f"  - {fa}: {reason}")
    else:
        print("Failed archives: 0 (All archives extracted cleanly!)")
    print("=" * 60)

if __name__ == '__main__':
    root_dir = os.path.dirname(os.path.abspath(__file__)) if len(sys.argv) < 2 else sys.argv[1]
    run_extraction_pipeline(root_dir)
