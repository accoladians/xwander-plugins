#!/usr/bin/env python3
"""
Example: Clone Ivalo Aurora Camp to create Rovaniemi Aurora Camp.

This script demonstrates the product cloning functionality of xwander-bokun.

Usage:
    # Dry run (preview without creating)
    doppler run -- python clone_aurora_camp.py --dry-run

    # Create the product
    doppler run -- python clone_aurora_camp.py

    # Create with custom description
    doppler run -- python clone_aurora_camp.py --description "Custom description..."
"""

import asyncio
import json
import sys
import argparse

# Add parent to path for local development
sys.path.insert(0, "/srv/plugins/xwander-bokun")

from xwander_bokun import BokunClient, clone_experience, CloneConfig


# Ivalo Aurora Camp product ID
SOURCE_PRODUCT_ID = 1107193

# Rovaniemi configuration
ROVANIEMI_CONFIG = CloneConfig(
    # New title for Rovaniemi version
    title="Aurora Camp Rovaniemi",

    # Location changes
    new_city="Rovaniemi",
    new_address_line1="Koskikatu 25",  # Example central Rovaniemi address
    new_postal_code="96200",
    new_latitude=66.5039,  # Rovaniemi city center
    new_longitude=25.7294,
    new_start_point_title="Xwander Nordic - Rovaniemi",

    # Updated description for Rovaniemi
    new_description="""
<p style="font-size:14px;line-height:1.6;color:#57646f;margin-top:0.5em;margin-bottom:0.5em">
<strong>20:00</strong> - Pick up from Rovaniemi city center hotels and transfer to Aurora Camp
</p>
<p style="font-size:14px;line-height:1.6;color:#57646f;margin-top:0.5em;margin-bottom:0.5em">
<strong>20:30</strong> - Arrive at Aurora Camp. Evening under the Arctic sky with open fire dinner
</p>
<p style="font-size:14px;line-height:1.6;color:#57646f;margin-top:0.5em;margin-bottom:0.5em">
<strong>22:30</strong> - Departure from Aurora Camp and transfer back to Rovaniemi (can be extended if Northern Lights are visible)
</p>
<p style="font-size:14px;line-height:1.6;color:#57646f;margin-top:0.5em;margin-bottom:0.5em">
<strong>23:00</strong> - Arrive back in Rovaniemi
</p>
""".strip(),

    new_excerpt="Aurora hunting and open fire dinner experience from Rovaniemi",

    # Add relevant flags
    add_flags=["NORTHERN_LIGHTS", "SMALL_GROUP"],

    # Add keywords for SEO
    add_keywords=[
        "rovaniemi",
        "aurora borealis",
        "northern lights",
        "arctic dinner",
        "lapland experience",
    ],

    # Keep as draft until reviewed
    keep_unpublished=True,
)


async def main(dry_run: bool = False, custom_description: str = None):
    """
    Clone Ivalo Aurora Camp to create Rovaniemi version.

    Args:
        dry_run: If True, show payload without creating
        custom_description: Optional custom description
    """
    print("\n" + "=" * 60)
    print("Cloning Ivalo Aurora Camp -> Rovaniemi Aurora Camp")
    print("=" * 60)

    config = ROVANIEMI_CONFIG
    if custom_description:
        config.new_description = custom_description

    print(f"\nSource product ID: {SOURCE_PRODUCT_ID}")
    print(f"New title: {config.title}")
    print(f"New location: {config.new_city}")
    print(f"Coordinates: {config.new_latitude}, {config.new_longitude}")

    async with BokunClient(debug=False) as client:
        print("\nConnecting to Bokun API...")

        # First, verify source product exists
        print(f"Fetching source product {SOURCE_PRODUCT_ID}...")
        source = await client.get_experience(SOURCE_PRODUCT_ID)
        print(f"✓ Found: {source.get('title')}")

        # Clone the product
        print("\nCloning product...")
        result = await clone_experience(
            client,
            SOURCE_PRODUCT_ID,
            config,
            dry_run=dry_run,
        )

        if dry_run:
            print("\n[DRY RUN] Would create product with payload:")
            payload = result.get("payload", {})
            print(f"  Title: {payload.get('title')}")
            print(f"  Location: {payload.get('locationCode', {}).get('name')}")
            print(f"  Flags: {payload.get('flags', [])}")
            print(f"  Keywords: {payload.get('keywords', [])}")
            print(f"  Published: {payload.get('published')}")

            # Save full payload for inspection
            with open("/tmp/rovaniemi-aurora-camp-payload.json", "w") as f:
                json.dump(payload, f, indent=2, default=str)
            print(f"\n  Full payload saved to: /tmp/rovaniemi-aurora-camp-payload.json")
        else:
            new_id = result.get("id")
            print(f"\n✓ Successfully created Rovaniemi Aurora Camp!")
            print(f"  New Product ID: {new_id}")
            print(f"  Status: Draft (unpublished)")
            print(f"\n  View at: https://xwander.bokun.io/experience/{new_id}")

            # Save result
            with open("/tmp/rovaniemi-aurora-camp-result.json", "w") as f:
                json.dump(result, f, indent=2, default=str)
            print(f"  Result saved to: /tmp/rovaniemi-aurora-camp-result.json")

            return new_id

    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Clone Ivalo Aurora Camp for Rovaniemi"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview without creating",
    )
    parser.add_argument(
        "--description",
        help="Custom description for the new product",
    )

    args = parser.parse_args()

    try:
        result = asyncio.run(main(
            dry_run=args.dry_run,
            custom_description=args.description,
        ))
        if result:
            print(f"\nNext steps:")
            print(f"  1. Review at https://xwander.bokun.io/experience/{result}")
            print(f"  2. Add photos and pricing")
            print(f"  3. Set up availability schedule")
            print(f"  4. Publish when ready")
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
