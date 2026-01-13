#!/bin/bash
# Example: Get complete campaign overview
#
# This script demonstrates getting a full overview of PMax campaigns
# including asset groups and search themes.

set -e

CUSTOMER_ID="2425288235"
CAMPAIGN_ID="23423204148"

echo "==================================================="
echo "  Xwander PMax Nordic - Campaign Overview"
echo "==================================================="
echo

# Get campaign details
echo "1. Campaign Details"
echo "-------------------"
xw ads pmax get --customer-id $CUSTOMER_ID --campaign-id $CAMPAIGN_ID
echo

# List all asset groups
echo "2. Asset Groups"
echo "---------------"
xw ads pmax list --customer-id $CUSTOMER_ID --asset-groups --campaign-id $CAMPAIGN_ID
echo

# Get search themes for each asset group
echo "3. Search Themes by Asset Group"
echo "--------------------------------"

echo "English (6655152002):"
THEMES_EN=$(xw ads pmax signals --customer-id $CUSTOMER_ID --asset-group-id 6655152002 list | grep -c '^\s*[0-9]' || echo 0)
echo "  Total themes: $THEMES_EN"
echo

echo "German (6655251007):"
THEMES_DE=$(xw ads pmax signals --customer-id $CUSTOMER_ID --asset-group-id 6655251007 list | grep -c '^\s*[0-9]' || echo 0)
echo "  Total themes: $THEMES_DE"
echo

echo "French (6655151999):"
THEMES_FR=$(xw ads pmax signals --customer-id $CUSTOMER_ID --asset-group-id 6655151999 list | grep -c '^\s*[0-9]' || echo 0)
echo "  Total themes: $THEMES_FR"
echo

echo "Spanish (6655250848):"
THEMES_ES=$(xw ads pmax signals --customer-id $CUSTOMER_ID --asset-group-id 6655250848 list | grep -c '^\s*[0-9]' || echo 0)
echo "  Total themes: $THEMES_ES"
echo

echo "==================================================="
echo "  Overview Complete"
echo "==================================================="
