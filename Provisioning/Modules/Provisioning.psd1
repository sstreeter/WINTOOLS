# Module Manifest for Provisioning
@{
    ModuleName = 'Provisioning'
    ModuleVersion = '1.0.0'
    GUID = 'ae6b8f42-7c8a-4d9e-9e12-3b4a5c6d7e8f'
    Author = 'Antigravity'
    CompanyName = 'WINTOOLS'
    FunctionsToExport = @(
        'Initialize-ProvisioningModule',
        'Test-ProvisioningPreflightChecks',
        'Show-ProvisioningMainMenu',
        'Perform-ProvisioningUserManagement',
        'Perform-ProvisioningComputerRename',
        'Perform-ProvisioningRemoteDesktop',
        'Perform-ProvisioningPowerSettings',
        'Perform-ProvisioningOpenSsh',
        'Get-ProvisioningKmsKeys',
        'Perform-ProvisioningActivation',
        'Perform-ProvisioningRollback',
        'Write-ProvisioningLog',
        'Show-ProvisioningSummary',
        'Save-ProvisioningLog'
    )
    VariablesToExport = @('Global:Summary')
}
