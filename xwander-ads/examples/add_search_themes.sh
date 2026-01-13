#!/bin/bash
# Example: Add search themes to all asset groups
#
# This script demonstrates bulk adding search themes to multiple asset groups
# for different languages in the Xwander PMax Nordic campaign.

set -e

CUSTOMER_ID="2425288235"

# Asset group IDs
AG_EN="6655152002"  # English
AG_DE="6655251007"  # German
AG_FR="6655151999"  # French
AG_ES="6655250848"  # Spanish

echo "Adding search themes to Xwander PMax Nordic asset groups..."
echo

# English themes
echo "Processing English asset group..."
cat > /tmp/themes-en.txt << 'EOF'
lapland tours
northern lights finland
rovaniemi activities
arctic wilderness experiences
midnight sun tours
husky sledding finland
reindeer farm visits
santa claus village
lapland winter holidays
finnish lapland adventures
EOF

xw ads pmax signals --customer-id $CUSTOMER_ID --asset-group-id $AG_EN bulk --file /tmp/themes-en.txt
echo "✓ English themes added"
echo

# German themes
echo "Processing German asset group..."
cat > /tmp/themes-de.txt << 'EOF'
lappland reisen
nordlichter finnland
rovaniemi aktivitäten
arktische wildnis
mitternachtssonne touren
huskyschlitten finnland
rentierfarm besuche
weihnachtsmann dorf
lappland winterurlaub
finnische lappland abenteuer
EOF

xw ads pmax signals --customer-id $CUSTOMER_ID --asset-group-id $AG_DE bulk --file /tmp/themes-de.txt
echo "✓ German themes added"
echo

# French themes
echo "Processing French asset group..."
cat > /tmp/themes-fr.txt << 'EOF'
circuits laponie
aurores boréales finlande
activités rovaniemi
expériences nature arctique
tours soleil de minuit
traîneau husky finlande
visites ferme rennes
village père noël
vacances hiver laponie
aventures laponie finlandaise
EOF

xw ads pmax signals --customer-id $CUSTOMER_ID --asset-group-id $AG_FR bulk --file /tmp/themes-fr.txt
echo "✓ French themes added"
echo

# Spanish themes
echo "Processing Spanish asset group..."
cat > /tmp/themes-es.txt << 'EOF'
tours laponia
auroras boreales finlandia
actividades rovaniemi
experiencias naturaleza ártica
tours sol medianoche
trineo huskies finlandia
visitas granja renos
aldea papá noel
vacaciones invierno laponia
aventuras laponia finlandesa
EOF

xw ads pmax signals --customer-id $CUSTOMER_ID --asset-group-id $AG_ES bulk --file /tmp/themes-es.txt
echo "✓ Spanish themes added"
echo

# Cleanup
rm -f /tmp/themes-*.txt

echo "All themes added successfully!"
echo
echo "Verify with:"
echo "  xw ads pmax signals --customer-id $CUSTOMER_ID --asset-group-id $AG_EN list"
