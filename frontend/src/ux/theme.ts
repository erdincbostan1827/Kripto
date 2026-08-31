import {createTheme} from '@mui/material/styles';

// Explicit high-contrast core tokens. Component-level browser/a11y acceptance is a
// separate external gate; these tokens make the minimum visual contrast auditable.
export const accessibleTokens={
  light:{background:'#FFFFFF',text:'#111827',primary:'#0057B8',onPrimary:'#FFFFFF',warning:'#7C2D12'},
  dark:{background:'#111827',text:'#F9FAFB',primary:'#93C5FD',onPrimary:'#111827',warning:'#FDBA74'}
} as const;

export const appTheme=createTheme({
  colorSchemes:{
    light:{palette:{background:{default:accessibleTokens.light.background},text:{primary:accessibleTokens.light.text},primary:{main:accessibleTokens.light.primary,contrastText:accessibleTokens.light.onPrimary}}},
    dark:{palette:{background:{default:accessibleTokens.dark.background},text:{primary:accessibleTokens.dark.text},primary:{main:accessibleTokens.dark.primary,contrastText:accessibleTokens.dark.onPrimary}}}
  },
  cssVariables:true,
  components:{MuiButton:{defaultProps:{disableElevation:true}}}
});
