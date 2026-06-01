"""
sample_dataset.py
-----------------
Generates a labelled sample dataset for training and evaluation.

Labels
------
  scam     : 1
  legitimate: 0

Sentiment categories (scammer sentiment)
-----------------------------------------
  urgent    : high-pressure, fear-driven language
  greedy    : lure of money / prize
  friendly  : false trust-building
  neutral   : no strong emotional tone
"""

import pandas as pd
import random

SCAM_MESSAGES = [
    # Urgent / fear-driven
    ("URGENT: Your account has been compromised. Click here immediately to verify your identity or your account will be suspended!", 1, "urgent"),
    ("WARNING! We detected unauthorized login from Russia. Confirm your details NOW to avoid losing access.", 1, "urgent"),
    ("Your bank account will be CLOSED in 24 hours unless you update your information. Act immediately!", 1, "urgent"),
    ("FINAL NOTICE: You owe outstanding taxes. Failure to pay today will result in arrest.", 1, "urgent"),
    ("Your Social Security Number has been suspended. Call us immediately to avoid legal consequences.", 1, "urgent"),
    ("ALERT: Your computer is infected with a virus. Call Microsoft Support NOW at 1-800-555-0199.", 1, "urgent"),
    ("Immediate action required: Your PayPal account is limited. Verify now or lose your funds.", 1, "urgent"),
    ("You have 2 hours to respond or your account will be permanently deleted. Click link to confirm.", 1, "urgent"),

    # Greedy / prize lure
    ("Congratulations! You have won $1,000,000 in our international lottery. Send your bank details to claim.", 1, "greedy"),
    ("You are selected as today's lucky winner! Claim your free iPhone 15 Pro by clicking this link.", 1, "greedy"),
    ("A wealthy Nigerian prince needs your help transferring $45 million. You will receive 30% for helping.", 1, "greedy"),
    ("Your email was selected in our random prize draw. You've won $500 Amazon gift card. Collect now!", 1, "greedy"),
    ("Invest just $100 today and make $10,000 in 7 days. Guaranteed returns. Join our crypto group.", 1, "greedy"),
    ("We found unclaimed inheritance money in your name worth $2.4 million. Contact us to retrieve it.", 1, "greedy"),
    ("You have been pre-approved for a $50,000 loan with no credit check. Apply in minutes, cash same day.", 1, "greedy"),
    ("Work from home and earn $5000 per week with no experience needed. Limited spots available!", 1, "greedy"),

    # Friendly / trust-building
    ("Hi, this is Sarah from customer support. I noticed your account and wanted to personally help you.", 1, "friendly"),
    ("Hey! I'm reaching out because our mutual friend recommended you. I have a great business opportunity.", 1, "friendly"),
    ("I know this might seem strange, but I really need someone trustworthy to help me with a sensitive matter.", 1, "friendly"),
    ("We've been helping people like you for 10 years. We just want to make sure you're protected.", 1, "friendly"),
    ("I found your profile and I think you'd be perfect for this. I hope we can build a friendship first.", 1, "friendly"),
    ("Don't tell anyone about this offer. It's only for a select few people I personally chose.", 1, "friendly"),

    # Phishing
    ("Dear customer, your Netflix subscription has expired. Update your payment method: http://netfIix-secure.com", 1, "urgent"),
    ("Your Amazon order has been placed. If this wasn't you, click here to cancel: http://amazoon-verify.net", 1, "urgent"),
    ("Chase Bank: Unusual activity detected. Secure your account at http://chase-secure-login.com/verify", 1, "urgent"),
    ("Your Apple ID has been locked. Unlock it now at: http://apple-id-verify-secure.com/unlock", 1, "urgent"),
    ("IRS Tax Refund: You are owed $3,240. Provide your direct deposit information to receive it.", 1, "greedy"),
    ("Congratulations! As a valued customer you qualify for a free cruise vacation. Call to claim!", 1, "greedy"),

    # Extended urgent / fear-driven
    ("SECURITY ALERT: Suspicious wire transfer blocked. Verify your identity within 1 hour.", 1, "urgent"),
    ("Your driver's license will be revoked unless you pay outstanding fines today.", 1, "urgent"),
    ("Court summons issued. Failure to appear will result in a warrant for your arrest.", 1, "urgent"),
    ("Your health insurance policy lapses tonight. Renew immediately to avoid coverage loss.", 1, "urgent"),
    ("We locked your credit card after fraud attempts. Call this number to unlock it now.", 1, "urgent"),
    ("Your student loan is in default. Pay now or face wage garnishment.", 1, "urgent"),
    ("Customs is holding your package. Pay the clearance fee within 12 hours.", 1, "urgent"),
    ("Your mortgage payment bounced. Avoid foreclosure by wiring funds today.", 1, "urgent"),
    ("Immigration notice: Your visa status requires immediate verification online.", 1, "urgent"),
    ("Your electricity will be disconnected tomorrow unless you pay the overdue balance.", 1, "urgent"),
    ("Police report filed under your name. Contact us immediately to dispute charges.", 1, "urgent"),
    ("Your Coinbase wallet has been flagged. Complete KYC verification in the next 30 minutes.", 1, "urgent"),
    ("Hospital bill overdue: Pay now or your account goes to collections.", 1, "urgent"),
    ("Your domain expires in 24 hours. Renew at this link to avoid losing your website.", 1, "urgent"),
    ("Child support enforcement: Pay outstanding balance or face license suspension.", 1, "urgent"),
    ("Your Uber account shows unpaid trips. Update billing or lose access permanently.", 1, "urgent"),
    ("FINRA notice: Your brokerage account requires urgent compliance review.", 1, "urgent"),
    ("Your passport application will be denied unless you confirm details immediately.", 1, "urgent"),

    # Extended greedy / prize lure
    ("You've been chosen for our exclusive Bitcoin airdrop. Send 0.1 ETH to claim 5 BTC.", 1, "greedy"),
    ("Secret shopper job: Earn $300 per assignment. Deposit required to start.", 1, "greedy"),
    ("Your late uncle left you $890,000. Pay the legal processing fee to release funds.", 1, "greedy"),
    ("Double your money in 48 hours with our forex signals. Join VIP group now.", 1, "greedy"),
    ("Free Tesla giveaway! You're entrant #7 of 10. Pay shipping to receive your car.", 1, "greedy"),
    ("Government grant approved: $12,000 available. Pay $199 activation fee to receive.", 1, "greedy"),
    ("You qualify for debt forgiveness. Pay a small admin fee to wipe all balances.", 1, "greedy"),
    ("Celebrity investment tip: Buy this penny stock before it explodes tomorrow.", 1, "greedy"),
    ("Your tax refund of $8,412 is ready. Enter bank info at this link to deposit.", 1, "greedy"),
    ("Mystery box worth $2000 for only $49. Limited stock — order before midnight.", 1, "greedy"),
    ("Become a brand ambassador: Free products plus $2000/week. Pay enrollment fee.", 1, "greedy"),
    ("You've won a Walmart sweepstakes. Provide SSN and routing number to claim prize.", 1, "greedy"),
    ("Passive income machine: Our bot trades for you. Minimum deposit $500.", 1, "greedy"),
    ("Inheritance from distant relative in Belgium. Lawyer fee of $2500 required first.", 1, "greedy"),
    ("Get rich with NFT flipping. Buy our course for $997 — guaranteed profit.", 1, "greedy"),
    ("Your credit score can jump 200 points. Pay $99 for our miracle repair service.", 1, "greedy"),
    ("Wholesale iPhones at 70% off. Wire payment to secure your bulk order.", 1, "greedy"),
    ("You were selected for a paid survey panel. Cash out after $50 registration.", 1, "greedy"),

    # Extended friendly / trust-building
    ("I've been watching your profile and think you're exactly who I need for this opportunity.", 1, "friendly"),
    ("My boss asked me to find someone honest like you. Can we talk privately?", 1, "friendly"),
    ("I don't usually reach out to strangers, but you seem really genuine.", 1, "friendly"),
    ("Let's keep this between us — I have insider information on a stock tip.", 1, "friendly"),
    ("I'm a soldier deployed overseas and need someone I can trust with my savings.", 1, "friendly"),
    ("We met on a dating app but I'm stuck abroad. Can you help me with travel costs?", 1, "friendly"),
    ("I'm a doctor volunteering abroad. I need you to receive a package for me.", 1, "friendly"),
    ("You're one of the few people I feel comfortable sharing this investment secret with.", 1, "friendly"),
    ("My grandmother left me gold bars but I need a local partner to receive them.", 1, "friendly"),
    ("I saw your LinkedIn — impressive background. I have a confidential offer for you.", 1, "friendly"),
    ("Please don't involve the bank yet. I trust you more than anyone else right now.", 1, "friendly"),
    ("I've helped dozens of people like you retire early. Let me mentor you personally.", 1, "friendly"),

    # Extended phishing / impersonation
    ("FedEx: Your package delivery failed. Reschedule at http://fedex-track-secure.net", 1, "urgent"),
    ("USPS: Undeliverable mail item. Confirm address: http://usps-redelivery.com", 1, "urgent"),
    ("Wells Fargo: Verify unusual login from Nigeria. http://wellsfargo-secure-verify.com", 1, "urgent"),
    ("DocuSign: You have a pending document to sign. http://docusign-docs-secure.net", 1, "urgent"),
    ("Microsoft 365: Your mailbox is full. Upgrade at http://office365-storage-update.com", 1, "urgent"),
    ("Spotify: Payment failed. Update card at http://spotify-billing-renew.com", 1, "urgent"),
    ("Venmo: Someone sent you $500. Claim at http://venmo-claim-payment.net", 1, "greedy"),
    ("Cash App: Your account received $1000. Verify at http://cashapp-verify-now.com", 1, "greedy"),
    ("LinkedIn: Your profile was viewed 500 times. Upgrade at http://linkedin-premium-offer.com", 1, "greedy"),
    ("WhatsApp: Your account will be deleted. Backup at http://whatsapp-backup-secure.net", 1, "urgent"),
    ("Instagram: Copyright violation on your account. Appeal at http://instagram-appeal-form.com", 1, "urgent"),
    ("Google: Unusual sign-in from China. Secure account: http://google-security-check.net", 1, "urgent"),
    ("Bank of America: Card locked. Unlock at http://bofa-card-unlock.com", 1, "urgent"),
    ("AT&T: Your bill is overdue. Pay now at http://att-bill-pay-secure.com", 1, "urgent"),
    ("TurboTax: Your refund is delayed. Update info at http://turbotax-refund-update.net", 1, "greedy"),
    ("eBay: You sold an item. Confirm payout at http://ebay-seller-payout-verify.com", 1, "greedy"),
    ("Zoom: Your meeting license expired. Renew at http://zoom-license-renewal.com", 1, "urgent"),
    ("Dropbox: Shared file requires password. Access at http://dropbox-file-share.net", 1, "urgent"),
    ("Your Walmart gift card balance expires today. Redeem at http://walmart-gift-redeem.net", 1, "greedy"),
    ("HMRC: You are due a tax rebate of £1,240. Submit bank details to receive payment.", 1, "greedy"),
    ("Your DHL shipment is on hold. Pay customs duty at http://dhl-customs-pay.com", 1, "urgent"),
]

LEGITIMATE_MESSAGES = [
    ("Hi! Can we reschedule our meeting to 3pm tomorrow? Let me know if that works.", 0, "neutral"),
    ("Your order #48291 has shipped and will arrive by Thursday. Track it on our website.", 0, "neutral"),
    ("Thanks for applying. We've reviewed your resume and would like to schedule an interview.", 0, "neutral"),
    ("Reminder: Your dentist appointment is on Friday at 10am. Reply to confirm or cancel.", 0, "neutral"),
    ("Hey, are you free this weekend? We're having a small get-together Saturday evening.", 0, "neutral"),
    ("Your monthly statement is ready to view online. As usual, no action is needed.", 0, "neutral"),
    ("The software update you requested has been completed. Please restart to apply changes.", 0, "neutral"),
    ("Hi, I just wanted to check in and see how you're doing. Hope everything is well!", 0, "neutral"),
    ("Please find attached the quarterly report we discussed in this morning's meeting.", 0, "neutral"),
    ("Your refund of $42.50 has been processed and will appear in 3-5 business days.", 0, "neutral"),
    ("Can you review the attached document before the end of day? Thanks in advance.", 0, "neutral"),
    ("Your library book is due back by next Monday. You can renew online to avoid a fine.", 0, "neutral"),
    ("Welcome to our newsletter! You can unsubscribe at any time from the footer link.", 0, "neutral"),
    ("The team is doing great work on the project. Keep it up, and let's sync next week.", 0, "neutral"),
    ("I'm following up on our conversation last week about the proposal. Any update?", 0, "neutral"),
    ("Your package was delivered to the front door at 2:14 PM. Photo confirmation attached.", 0, "neutral"),
    ("Just a heads-up, the office will be closed on Monday for the public holiday.", 0, "neutral"),
    ("Your 2-factor authentication code is 847291. This code expires in 10 minutes.", 0, "neutral"),
    ("We've received your support ticket #10284. Our team will get back to you within 24 hours.", 0, "neutral"),
    ("Congrats on completing the course! Your certificate has been sent to your email.", 0, "neutral"),
    ("The meeting notes from Tuesday's session have been shared in the project folder.", 0, "neutral"),
    ("New comment on your post: 'Great analysis! Really appreciated the detailed breakdown.'", 0, "neutral"),
    ("Your payment of $120.00 was received successfully. Receipt ID: TXN-2024-88219.", 0, "neutral"),
    ("Looking forward to seeing you at the conference next month! Let's connect there.", 0, "neutral"),
    ("Your subscription renews automatically on the 15th. Manage it in account settings.", 0, "neutral"),
    ("I finished reviewing the codebase — left some comments in the pull request.", 0, "neutral"),
    ("The weather looks great this weekend. Want to plan that hike we talked about?", 0, "neutral"),
    ("Our records show your warranty is still valid. Contact us if you need any support.", 0, "neutral"),
    ("Your friend Alice shared a photo album with you. Click to view it.", 0, "neutral"),
    ("We wanted to thank you for your continued support. Here's 10% off your next order.", 0, "neutral"),

    # Extended legitimate messages
    ("The project deadline has been moved to next Wednesday. Please update your tasks.", 0, "neutral"),
    ("Your flight AA 1842 departs at 6:45 AM from Gate B12. Check in online.", 0, "neutral"),
    ("Parking validation is available at the front desk for visitors.", 0, "neutral"),
    ("The cafeteria menu for this week is posted on the intranet.", 0, "neutral"),
    ("Your prescription is ready for pickup at the pharmacy on Main Street.", 0, "neutral"),
    ("The HOA meeting is scheduled for Tuesday at 7 PM in the community room.", 0, "neutral"),
    ("Your car service appointment is confirmed for Saturday at 9 AM.", 0, "neutral"),
    ("The webinar recording from yesterday is now available in the learning portal.", 0, "neutral"),
    ("Please bring your ID to the front desk when you arrive for your appointment.", 0, "neutral"),
    ("Your gym membership renews on the first of next month.", 0, "neutral"),
    ("The IT department will perform maintenance Sunday from 2-4 AM.", 0, "neutral"),
    ("Your child's school picture day is next Thursday.", 0, "neutral"),
    ("The team lunch is at noon in the break room. Pizza will be provided.", 0, "neutral"),
    ("Your electric bill of $87.43 is due on the 15th. Pay online or by mail.", 0, "neutral"),
    ("The book you reserved is now available at the downtown branch.", 0, "neutral"),
    ("Your Uber ride receipt for $24.50 is attached for your records.", 0, "neutral"),
    ("The conference room booking for 2 PM has been confirmed.", 0, "neutral"),
    ("Your password was changed successfully. If this wasn't you, contact IT.", 0, "neutral"),
    ("The annual performance review forms are due by end of month.", 0, "neutral"),
    ("Your hotel reservation at Marriott is confirmed for March 12-14.", 0, "neutral"),
    ("The soccer practice for U12 has been moved to Field 3.", 0, "neutral"),
    ("Your water bill autopay processed for $42.18.", 0, "neutral"),
    ("The new employee orientation starts at 9 AM in Room 204.", 0, "neutral"),
    ("Your Spotify family plan invite was accepted by two members.", 0, "neutral"),
    ("The vet appointment for Max is Thursday at 3:30 PM.", 0, "neutral"),
    ("Your Costco order is ready for pickup at the warehouse.", 0, "neutral"),
    ("The PTA fundraiser raised $2,400. Thank you for participating.", 0, "neutral"),
    ("Your LinkedIn connection request from Jane was accepted.", 0, "neutral"),
    ("The building fire alarm test is scheduled for Friday at 10 AM.", 0, "neutral"),
    ("Your DoorDash order from Thai Garden is on the way. ETA 25 minutes.", 0, "neutral"),
    ("The scholarship application deadline is April 1. Submit documents early.", 0, "neutral"),
    ("Your Tesla software update v12.3 installed successfully overnight.", 0, "neutral"),
    ("The neighborhood block party is Saturday from 4-8 PM.", 0, "neutral"),
    ("Your 401k contribution for this pay period was $450.", 0, "neutral"),
    ("The yoga class you registered for starts Monday at 6 PM.", 0, "neutral"),
    ("Your Instacart shopper is checking out. Delivery in about 45 minutes.", 0, "neutral"),
    ("The board meeting agenda has been circulated for review.", 0, "neutral"),
    ("Your passport renewal application was received by the State Department.", 0, "neutral"),
    ("The pool will close for cleaning on Wednesday afternoon.", 0, "neutral"),
    ("Your Audible credit is available. Browse new releases in the app.", 0, "neutral"),
    ("The volunteer shift sign-up sheet is in the break room.", 0, "neutral"),
    ("Your Grubhub order from Chipotle has been delivered to your door.", 0, "neutral"),
    ("The software license for Adobe Creative Cloud renews next month.", 0, "neutral"),
    ("Your parking permit for Lot C expires at the end of the semester.", 0, "neutral"),
    ("The blood drive is in the lobby from 10 AM to 2 PM tomorrow.", 0, "neutral"),
    ("Your Hulu subscription will renew for $17.99 on the 20th.", 0, "neutral"),
    ("The contractor will arrive between 8-10 AM for the kitchen repair.", 0, "neutral"),
    ("Your student ID card is ready at the campus card office.", 0, "neutral"),
    ("The book club selection for March is available at the library.", 0, "neutral"),
    ("Your AAA roadside assistance membership is active through 2027.", 0, "neutral"),
    ("The office potluck signup list is on the shared drive.", 0, "neutral"),
    ("Your Zelle payment of $75 to Mike was sent successfully.", 0, "neutral"),
    ("The parent-teacher conference slots are open for booking online.", 0, "neutral"),
    ("Your Apple Watch workout summary for the week is ready to view.", 0, "neutral"),
    ("The recycling pickup schedule changes next week due to the holiday.", 0, "neutral"),
    ("Your OpenTable reservation for 4 at 7:30 PM is confirmed.", 0, "neutral"),
    ("The flu shot clinic is available walk-in at the health center.", 0, "neutral"),
    ("Your GitHub pull request #42 received two approving reviews.", 0, "neutral"),
    ("The museum tickets for Saturday at 2 PM are in your email.", 0, "neutral"),
    ("Your pet's vaccination records were updated at the last visit.", 0, "neutral"),
    ("The shuttle bus departs every 15 minutes from Terminal B.", 0, "neutral"),
    ("Your Calendly meeting with the recruiter is set for Tuesday 11 AM.", 0, "neutral"),
    ("The farmers market opens at 8 AM this Saturday downtown.", 0, "neutral"),
    ("Your Nest thermostat detected you left home and switched to eco mode.", 0, "neutral"),
    ("The coding bootcamp cohort starts orientation on the first Monday.", 0, "neutral"),
    ("Your REI dividend of $32.50 is available to use in store or online.", 0, "neutral"),
    ("The community garden plot assignment for spring is posted.", 0, "neutral"),
    ("Your Slack workspace admin approved the new channel request.", 0, "neutral"),
    ("The dry cleaning will be ready after 5 PM today.", 0, "neutral"),
    ("Your Venmo payment request to Sarah for $28 was declined.", 0, "neutral"),
    ("The town hall meeting minutes from last week are posted on the city website.", 0, "neutral"),
    ("Your bicycle tune-up at the shop is complete. Pick up anytime before 6 PM.", 0, "neutral"),
    ("The weather advisory for heavy rain tomorrow may affect outdoor events.", 0, "neutral"),
]


def build_dataset(extra_noise: float = 0.0) -> pd.DataFrame:
    """
    Returns a DataFrame with columns: [text, label, sentiment_label].

    Parameters
    ----------
    extra_noise : float
        If > 0, randomly flip this fraction of labels to simulate noisy data.
    """
    all_data = SCAM_MESSAGES + LEGITIMATE_MESSAGES
    random.shuffle(all_data)

    df = pd.DataFrame(all_data, columns=["text", "label", "sentiment_label"])

    if extra_noise > 0:
        n_flip = int(len(df) * extra_noise)
        flip_idx = random.sample(range(len(df)), n_flip)
        df.loc[flip_idx, "label"] = 1 - df.loc[flip_idx, "label"]

    return df


if __name__ == "__main__":
    df = build_dataset()
    print(df.groupby(["label", "sentiment_label"]).size())
    df.to_csv("sample_data.csv", index=False)
    print("Saved sample_data.csv")
