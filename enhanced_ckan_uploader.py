#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import argparse
import sys
from ckanapi import RemoteCKAN, errors as ckanapi_errors
from dotenv import load_dotenv

load_dotenv()  # Загружаем переменные из .env


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Upload CSV file to a dataset on CKAN portal (creates dataset if it does not exist)')

    # Required arguments
    parser.add_argument('--host', required=True, help='CKAN portal hostname (e.g., data.opengov.kz)')
    parser.add_argument('--token', required=False, help='API token (or use CKAN_TOKEN from .env)')
    parser.add_argument('--file', required=True, help='CSV file to upload')
    parser.add_argument('--dataset', required=True, help='Dataset ID to upload to (will be created if not exists)')
    parser.add_argument('--org', required=True, help='Organization ID the dataset belongs to')

    # Optional arguments
    parser.add_argument('--resource-name', help='Name for the resource (defaults to filename)')
    parser.add_argument('--resource-desc', default='News data from Kazakhstan government portals',
                        help='Description for the resource')
    parser.add_argument('--source', default='https://www.gov.kz',
                        help='Source URL for the dataset')
    parser.add_argument('--author', default='Data Collector',
                        help='Author name')
    parser.add_argument('--email', required=True,
                        help='Author email')
    parser.add_argument('--dataset-title', help='Title for the dataset if it needs to be created')
    parser.add_argument('--dataset-desc', help='Description for the dataset if it needs to be created')
    parser.add_argument('--tags', default='news,government,kazakhstan,ministries',
                        help='Comma-separated tags')
    parser.add_argument('--delay', type=int, default=1,
                        help='Delay between API requests in seconds (default: 1)')
    parser.add_argument('--update-metadata', action='store_true',
                        help='Update dataset metadata (default: False)')

    return parser.parse_args()


def check_organization(ckan, org_id, delay):
    try:
        org = ckan.action.organization_show(id=org_id)
        print(f"Organization '{org_id}' exists: {org['title']}")
        time.sleep(delay)
        return True
    except ckanapi_errors.NotFound:
        print(f"ERROR: Organization '{org_id}' not found.")
        return False
    except ckanapi_errors.CKANAPIError as e:
        print(f"ERROR checking organization: {e}")
        return False


def check_dataset(ckan, dataset_id, delay):
    try:
        dataset = ckan.action.package_show(id=dataset_id)
        print(f"Dataset '{dataset_id}' exists: {dataset['title']}")
        time.sleep(delay)
        return dataset
    except ckanapi_errors.NotFound:
        print(f"Dataset '{dataset_id}' not found.")
        return None
    except ckanapi_errors.CKANAPIError as e:
        print(f"ERROR checking dataset: {e}")
        return None


def create_dataset(ckan, dataset_id, org_id, title, description, source, author, email, tags_list, delay):
    try:
        if not title:
            title = f"Dataset {dataset_id}"

        if not description:
            description = f"Data collection for {dataset_id}"

        print(f"Creating new dataset '{dataset_id}'...")

        dataset = ckan.action.package_create(
            name=dataset_id,
            title=title,
            notes=description,
            owner_org=org_id,
            extras=[
                {"key": "Source", "value": source},
                {"key": "Author", "value": author},
                {"key": "Author Email", "value": email}
            ],
            tags=[{"name": tag.strip()} for tag in tags_list]
        )
        print(f"Dataset '{dataset_id}' created successfully with title: {title}")
        time.sleep(delay)
        return dataset
    except ckanapi_errors.ValidationError as e:
        print(f"ERROR creating dataset: {e}")
        return None
    except ckanapi_errors.CKANAPIError as e:
        print(f"ERROR creating dataset: {e}")
        return None


def update_dataset_metadata(ckan, dataset_id, org_id, source, author, email, tags_list, delay):
    try:
        dataset = ckan.action.package_update(
            id=dataset_id,
            owner_org=org_id,
            extras=[
                {"key": "Source", "value": source},
                {"key": "Author", "value": author},
                {"key": "Author Email", "value": email}
            ],
            tags=[{"name": tag.strip()} for tag in tags_list]
        )
        print(f"Dataset '{dataset_id}' metadata updated successfully")
        time.sleep(delay)
        return dataset
    except ckanapi_errors.CKANAPIError as e:
        print(f"ERROR updating dataset metadata: {e}")
        return None


def upload_resource(ckan, dataset_id, filepath, resource_name, resource_desc, delay):
    if not os.path.exists(filepath):
        print(f"ERROR: File '{filepath}' does not exist")
        return False

    if not resource_name:
        resource_name = os.path.basename(filepath)

    timestamp = time.strftime('%Y-%m-%d')

    try:
        resources = ckan.action.package_show(id=dataset_id)["resources"]

        for resource in resources:
            if resource["name"] == resource_name:
                print(f"Resource '{resource_name}' exists, updating...")
                with open(filepath, 'rb') as file_content:
                    ckan.action.resource_update(
                        id=resource["id"],
                        name=resource_name,
                        upload=file_content,
                        format="CSV",
                        description=f"{resource_desc} (updated on {timestamp})"
                    )
                print(f"Resource '{resource_name}' updated")
                time.sleep(delay)
                return True

        print(f"Creating new resource '{resource_name}'...")
        with open(filepath, 'rb') as file_content:
            ckan.action.resource_create(
                package_id=dataset_id,
                name=resource_name,
                upload=file_content,
                format="CSV",
                description=f"{resource_desc} (created on {timestamp})"
            )
        print(f"Resource '{resource_name}' created")
        time.sleep(delay)
        return True

    except ckanapi_errors.CKANAPIError as e:
        print(f"ERROR uploading/updating resource: {e}")
        return False


def main():
    args = parse_arguments()

    # Поддержка .env переменной CKAN_TOKEN
    if not args.token:
        args.token = os.getenv("CKAN_TOKEN")

    if not args.token:
        print("ERROR: API token is required. Provide via --token or CKAN_TOKEN env variable.")
        sys.exit(1)

    ckan_url = f"https://{args.host}"

    try:
        print(f"Connecting to CKAN at {ckan_url}")
        ckan = RemoteCKAN(ckan_url, apikey=args.token)
    except Exception as e:
        print(f"ERROR connecting to CKAN: {e}")
        sys.exit(1)

    if not check_organization(ckan, args.org, args.delay):
        sys.exit(1)

    dataset = check_dataset(ckan, args.dataset, args.delay)

    # Create dataset if it doesn't exist
    if not dataset:
        print(f"Attempting to create dataset '{args.dataset}'...")
        dataset = create_dataset(
            ckan,
            args.dataset,
            args.org,
            args.dataset_title,
            args.dataset_desc,
            args.source,
            args.author,
            args.email,
            args.tags.split(','),
            args.delay
        )

        if not dataset:
            print("Dataset creation failed. Exiting.")
            sys.exit(1)
    elif args.update_metadata:
        print(f"Updating metadata for dataset '{args.dataset}'...")
        tags_list = args.tags.split(',')
        update_dataset_metadata(
            ckan, args.dataset, args.org,
            args.source, args.author, args.email,
            tags_list, args.delay
        )

    print(f"Uploading file '{args.file}' to dataset '{args.dataset}'...")
    success = upload_resource(
        ckan,
        args.dataset,
        args.file,
        args.resource_name,
        args.resource_desc,
        args.delay
    )

    if success:
        print("✅ CSV upload completed successfully")
        print(f"Dataset URL: https://{args.host}/dataset/{args.dataset}")
    else:
        print("❌ CSV upload failed")
        sys.exit(1)


if __name__ == "__main__":
    main()