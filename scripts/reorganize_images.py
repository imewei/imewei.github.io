#!/usr/bin/env python3
"""
Image Reorganization Script for MSD Soft Matter Lab Site

This script reorganizes images from the imported folder structure to categorized folders,
creates descriptive filenames, and generates an image manifest.

Categories:
- team/: Profile photos from our-team/ and wei-chen/ folders
- research/: Research diagrams from research/ folder
- facilities/: Equipment images from facilities/ folder
- general/: Hero images, logos, misc from home/, contact/, links/, publications/
"""

import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def get_file_type(filepath: str) -> str:
    """Use the 'file' command to determine actual file type."""
    result = subprocess.run(['file', filepath], capture_output=True, text=True)
    return result.stdout


def is_valid_image(filepath: str) -> bool:
    """Check if a file is a valid image (not HTML error page)."""
    file_type = get_file_type(filepath)
    return any(img_type in file_type for img_type in ['JPEG', 'PNG', 'GIF', 'image data'])


def get_proper_extension(filepath: str) -> str:
    """Determine the correct file extension based on actual file type."""
    file_type = get_file_type(filepath)
    if 'PNG' in file_type:
        return '.png'
    elif 'JPEG' in file_type:
        return '.jpg'
    elif 'GIF' in file_type:
        return '.gif'
    return Path(filepath).suffix.lower() or '.jpg'


def categorize_by_source_folder(source_folder: str) -> str:
    """Determine category based on source folder."""
    folder_to_category = {
        'our-team': 'team',
        'wei-chen': 'team',
        'research': 'research',
        'facilities': 'facilities',
        'home': 'general',
        'contact': 'general',
        'links': 'general',
        'publications': 'general',
    }
    return folder_to_category.get(source_folder, 'general')


def is_hero_image(filename: str) -> bool:
    """Check if this is the common hero banner image."""
    hero_hash = 'AAzXCkfT2Sxyo0HSmMefO14TqB_vaDWHPfcK5dS3qI9NvrmZ9q0bxKEW82KtSxUkef0et5MxX2LffJG-MTTm6k5VXUNVhYEemE4fuO0RX2QX8YEHMyuANmO_Ko38ocXAnj5BGF50_6zwEA2MxwYyS86vkbfyz4cQmfaERNFmju7eyb1JFGmFe1a8HVFYgUE'
    return hero_hash in filename


def main():
    base_dir = Path('/Users/b80985/Documents/GitHub/imewei.github.io/assets/img')
    imported_dir = base_dir / 'imported'

    # Target directories
    target_dirs = {
        'team': base_dir / 'team',
        'research': base_dir / 'research',
        'facilities': base_dir / 'facilities',
        'general': base_dir / 'general',
    }

    # Clean existing target directories
    for target_dir in target_dirs.values():
        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.mkdir(exist_ok=True)

    hero_copied = False

    # Manifest data
    manifest = {
        'generated': datetime.now(timezone.utc).isoformat(),
        'description': 'Image manifest for MSD Soft Matter Lab website migration',
        'categories': {
            'team': 'Profile photos of lab members',
            'research': 'Research area diagrams and figures',
            'facilities': 'Lab equipment and facility images',
            'general': 'Hero images, logos, and miscellaneous',
        },
        'images': [],
        'invalid_files': [],
    }

    # Counters for generating names per category
    name_counters = {'team': 0, 'research': 0, 'facilities': 0, 'general': 0}

    # Process each source folder
    source_folders = ['our-team', 'wei-chen', 'research', 'facilities', 'home', 'contact', 'links', 'publications']

    for source_folder in source_folders:
        source_path = imported_dir / source_folder
        if not source_path.exists():
            continue

        # Base category for this folder
        base_category = categorize_by_source_folder(source_folder)

        for file_path in sorted(source_path.iterdir()):
            if file_path.name.startswith('.'):
                continue

            original_name = file_path.stem

            # Check if valid image
            if not is_valid_image(str(file_path)):
                manifest['invalid_files'].append({
                    'original_path': str(file_path.relative_to(base_dir)),
                    'source_page': source_folder,
                    'reason': 'HTML error page (not an actual image)',
                })
                continue

            # Determine category and target directory for THIS image
            if is_hero_image(original_name):
                if hero_copied:
                    continue  # Skip duplicate hero images
                hero_copied = True
                category = 'general'
                new_name = 'hero-banner'
            else:
                category = base_category
                # Generate descriptive name if needed
                if original_name.startswith('AAzXCk'):
                    name_counters[category] += 1
                    prefix_map = {
                        'team': 'team-member',
                        'research': 'research-diagram',
                        'facilities': 'equipment',
                        'general': 'general-image',
                    }
                    new_name = f"{prefix_map[category]}-{name_counters[category]:02d}"
                else:
                    # Already has a descriptive name
                    new_name = original_name

            target_dir = target_dirs[category]

            # Get proper extension
            extension = get_proper_extension(str(file_path))
            new_filename = f"{new_name}{extension}"
            target_path = target_dir / new_filename

            # Handle name conflicts
            if target_path.exists():
                if file_path.stat().st_size == target_path.stat().st_size:
                    continue  # Same file, skip
                counter = 2
                while target_path.exists():
                    new_filename = f"{new_name}-{counter}{extension}"
                    target_path = target_dir / new_filename
                    counter += 1

            # Copy file to new location
            shutil.copy2(str(file_path), str(target_path))

            # Record in manifest
            manifest['images'].append({
                'original_path': str(file_path.relative_to(base_dir)),
                'new_path': str(target_path.relative_to(base_dir)),
                'category': category,
                'source_page': source_folder,
                'original_filename': file_path.name,
                'new_filename': new_filename,
                'file_size': target_path.stat().st_size,
            })

    # Add summary statistics
    manifest['summary'] = {
        'total_images': len(manifest['images']),
        'invalid_files': len(manifest['invalid_files']),
        'by_category': {
            cat: len([img for img in manifest['images'] if img['category'] == cat])
            for cat in ['team', 'research', 'facilities', 'general']
        },
    }

    # Write manifest
    manifest_path = base_dir / 'image-manifest.json'
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    print("Image reorganization complete!")
    print(f"Total images copied: {manifest['summary']['total_images']}")
    print(f"Invalid files skipped: {manifest['summary']['invalid_files']}")
    print(f"By category: {manifest['summary']['by_category']}")
    print(f"Manifest saved to: {manifest_path}")

    return manifest


if __name__ == '__main__':
    main()
