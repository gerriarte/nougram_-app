
import { quoteService } from '@/services/quoteService';
import { PublicQuoteView } from '@/components/quotes/public/PublicQuoteView';
import { notFound } from 'next/navigation';
import { Metadata } from 'next';

type Props = {
    params: { token: string }
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
    const quote = await quoteService.getQuoteByToken(params.token);
    if (!quote) return { title: 'Propuesta no encontrada' };

    return {
        title: `Propuesta Comercial: ${quote.project} - Nougram`,
        description: `Propuesta preparada para ${quote.client}`
    };
}

export default async function ProposalPage({ params }: Props) {
    const quote = await quoteService.getQuoteByToken(params.token);

    if (!quote) {
        notFound();
    }

    return <PublicQuoteView quote={quote} />;
}
