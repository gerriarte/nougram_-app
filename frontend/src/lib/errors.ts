/**
 * Business error for 402 Payment Required (insufficient credits).
 * UI can show PaywallModal when this is caught.
 */
export class CreditsRequiredError extends Error {
  readonly statusCode = 402;
  constructor(
    message: string,
    public readonly availableCredits?: number,
    public readonly requiredCredits?: number
  ) {
    super(message);
    this.name = "CreditsRequiredError";
    Object.setPrototypeOf(this, CreditsRequiredError.prototype);
  }
}
