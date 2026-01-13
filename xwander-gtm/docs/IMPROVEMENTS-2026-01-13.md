# xwander-gtm Plugin Improvements

**Date**: 2026-01-13
**Based on**: Product Type Conversions implementation session
**Priority**: High - these issues caused failures during GTM configuration

---

## Issue 1: Wrong Variable Type for User-Provided Data (CRITICAL)

**Location**: `xwander_gtm/variables.py:160`

**Problem**: The `create_user_data_variable()` method uses type `gtes` (Google Tag Enhanced Settings), but the actual working User-Provided Data variable in GTM uses type `awec`.

**Current Code**:
```python
variable_body = {
    'name': name,
    'type': 'gtes',  # WRONG TYPE
    'parameter': []
}
```

**Evidence**: Existing working variable in GTM-K8ZTWM4C:
```json
{
  "variableId": "6",
  "name": "User-Provided Data",
  "type": "awec",  // CORRECT TYPE
  "parameter": [
    {"type": "template", "key": "mode", "value": "AUTO"},
    {"type": "boolean", "key": "autoPhoneEnabled", "value": "true"},
    {"type": "boolean", "key": "autoAddressEnabled", "value": "true"},
    {"type": "boolean", "key": "autoEmailEnabled", "value": "true"}
  ]
}
```

**Impact**: Variables created with `gtes` type have no parameters and cause GTM compiler errors when creating versions.

**Fix**:
```python
variable_body = {
    'name': name,
    'type': 'awec',  # Google Ads Enhanced Conversions
    'parameter': []
}

if auto_mode:
    variable_body['parameter'].extend([
        {'type': 'template', 'key': 'mode', 'value': 'AUTO'},
        {'type': 'boolean', 'key': 'autoPhoneEnabled', 'value': 'true'},
        {'type': 'boolean', 'key': 'autoAddressEnabled', 'value': 'true'},
        {'type': 'boolean', 'key': 'autoEmailEnabled', 'value': 'true'},
        {'type': 'boolean', 'key': 'enableElementBlocking', 'value': 'false'}
    ])
else:
    # Manual mode with variable references
    variable_body['parameter'].extend([
        {'type': 'template', 'key': 'mode', 'value': 'MANUAL'},
        # ... field mappings using GTM variable syntax {{Variable Name}}
    ])
```

---

## Issue 2: No Version Creation Validation

**Location**: `xwander_gtm/workspace.py:136`

**Problem**: When version creation fails with a "compiler error", there's no detail about what's wrong.

**Current Behavior**:
```
Error: Version creation failed with compiler error: True
```

**Desired Behavior**:
```
Error: Version creation failed with compiler error
  - Variable 94 (EC - Product Form Data): Missing required parameter 'mode'
  - Tag 97: References undefined variable '{{EC - Product Form Data}}'
```

**Fix**: Add a `validate_workspace()` method that checks:
1. All referenced variables exist
2. All variable types have required parameters
3. All triggers have valid conditions
4. All tags have valid trigger references

---

## Issue 3: Missing Conversion Label Retrieval

**Problem**: When creating conversion tags, we need the conversion label from Google Ads API, but have to make separate API calls.

**Current Workflow**:
1. Create conversion action in Google Ads → get ID
2. Query Google Ads API for label
3. Create GTM tag with ID + label

**Desired**:
```python
# Integrated helper
label = gtm_client.get_conversion_label(google_ads_customer_id, conversion_action_id)
```

**Fix**: Add integration with Google Ads API or cache conversion labels in knowledge/conversions.json.

---

## Issue 4: No Atomic/Batch Operations

**Problem**: Creating multiple resources (variables, triggers, tags) requires separate API calls that can partially fail.

**Current**:
```python
var1 = var_mgr.create_variable(...)  # Success
var2 = var_mgr.create_variable(...)  # Success
trigger = trigger_mgr.create_trigger(...)  # Fails - rate limit
# Now have orphaned variables
```

**Desired**:
```python
# Atomic operation
resources = gtm_client.create_batch([
    {'type': 'variable', 'config': {...}},
    {'type': 'variable', 'config': {...}},
    {'type': 'trigger', 'config': {...}},
    {'type': 'tag', 'config': {...}}
])
# Either all succeed or all fail
```

**Note**: GTM API doesn't support true batch operations, but we can implement client-side rollback.

---

## Issue 5: CLI Help Could Be More Descriptive

**Problem**: `xw gtm create-ec-variable --help` doesn't explain the difference between AUTO and MANUAL mode.

**Fix**: Add examples and mode explanations to CLI help text:
```
--auto-mode / --manual-mode
    AUTO: Google automatically detects form fields (recommended for standard forms)
    MANUAL: Specify exact dataLayer variable mappings (for custom implementations)

    Example AUTO: xw gtm create-ec-variable --name "EC - Forms"
    Example MANUAL: xw gtm create-ec-variable --name "EC - Custom" --manual-mode \
        --email-var "{{DLV - email}}" --phone-var "{{DLV - phone}}"
```

---

## Issue 6: No Dry-Run Mode for Complex Operations

**Problem**: Can't preview what will be created before actually creating it.

**Desired**:
```bash
xw gtm create-conversion-setup --config setup.json --dry-run

Would create:
  Variables: 6
    - DLV - product_type (v)
    - DLV - hs_form_guid (v)
    ...
  Triggers: 2
    - HubSpot Form - Day Tour (customEvent)
    - HubSpot Form - Multiday Package (customEvent)
  Tags: 2
    - Google Ads - Day Tours Conversion (awct)
    - Google Ads - Multiday Package Conversion (awct)

Run without --dry-run to create.
```

---

## Issue 7: Enhanced Conversions Reference Should Use Variable ID

**Location**: `xwander_gtm/tags.py:320`

**Problem**: EC variable reference uses name syntax `{{Variable Name}}` but if the variable name has special characters or spaces, it can fail.

**Current**:
```python
params.append({
    'type': 'template',
    'key': 'cssProvidedEnhancedConversionValue',
    'value': f"{{{{{user_data_variable}}}}}"  # {{User-Provided Data}}
})
```

**Safer**: Validate variable exists first, or use variable ID reference.

---

## Recommended Priority

1. **CRITICAL**: Fix `awec` vs `gtes` type issue (Issue 1) - ✅ FIXED (2026-01-13)
2. **HIGH**: Add workspace validation (Issue 2) - ✅ FIXED (2026-01-13)
3. **MEDIUM**: Add dry-run mode (Issue 6) - ✅ FIXED (2026-01-13)
4. **MEDIUM**: Improve CLI help (Issue 5) - ✅ FIXED (2026-01-13)
5. **LOW**: Batch operations (Issue 4)
6. **LOW**: Conversion label integration (Issue 3)

---

## Fixes Implemented (2026-01-13)

### P0 Fix: EC Variable Type (`variables.py`)
- Changed type from `gtes` to `awec` (Google Ads Web Enhanced Conversions)
- Added proper AUTO mode parameters: `mode=AUTO`, `autoPhoneEnabled`, `autoAddressEnabled`, `autoEmailEnabled`
- Added MANUAL mode support with GTM variable references (`email_var`, `phone_var`, etc.)
- Added comprehensive docstring with examples

### P1 Fix: Workspace Validation (`workspace.py`)
- Added `validate_workspace()` method that checks:
  - `awec` variables have required `mode` parameter
  - `gtes` variables trigger warning (wrong type for EC)
  - All variable references `{{...}}` resolve to existing variables
  - All trigger references in tags are valid
  - Conversion tags have required `conversionId` and `conversionLabel`
- Integrated validation into `create_version()` - runs by default before version creation
- Clear error messages with resource type, ID, name, and specific issue

### P2 Fix: Dry-Run Mode & CLI Improvements (`cli.py`)
- Added `--dry-run` to `create-version` command - previews changes without creating
- Added `--skip-validation` to `create-version` command (not recommended)
- Added `validate-workspace` command for standalone validation
- Updated `create-ec-variable` with:
  - Better help text explaining AUTO vs MANUAL modes
  - `--email-var`, `--phone-var`, `--first-name-var`, `--last-name-var` options for MANUAL mode
  - `--dry-run` flag to preview variable structure
  - Examples in help text

---

## Testing Checklist After Fixes

- [ ] `create_user_data_variable()` creates variable with type `awec`
- [ ] AUTO mode creates variable with correct parameters
- [ ] MANUAL mode creates variable with dataLayer mappings
- [ ] `create_version()` provides detailed error on failure
- [ ] EC-enabled tags can reference created variables
- [ ] GTM version creation succeeds after fix

---

## Session Notes

During the 2026-01-13 session, the gemini-agent created a variable with type `gtes` that had no parameters. This caused:
1. GTM version creation to fail with "compiler error"
2. Had to delete the broken variable (ID 94)
3. Had to update tags (97, 98) to use existing `User-Provided Data` variable (ID 6)
4. Version creation succeeded only after cleanup

Total time lost: ~15 minutes debugging + fixing
