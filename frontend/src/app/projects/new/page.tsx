import { redirect } from 'next/navigation';
import { CANONICAL_NEW_QUOTE_PATH } from '@/lib/mobile-routes';

/**
 * Legacy URL: single canonical entry for new quotes (see mobile routing plan).
 */
export default function NewProjectRedirectPage() {
    redirect(CANONICAL_NEW_QUOTE_PATH);
}
