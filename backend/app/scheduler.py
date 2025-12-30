from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, date, timedelta
from app.db import db
import logging

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def generate_recurring_expenses():
    """
    Background job that runs daily to generate expenses from recurring templates.
    Checks each active recurring expense and creates an expense if due.
    """
    logger.info("Running recurring expenses generation job")
    
    try:
        today = date.today()
        
        # Get all active recurring expenses
        recurring = await db.fetch_all(
            """
            SELECT id, user_id, category_id, amount, currency, description,
                   frequency, start_date, last_generated_date
            FROM recurring_expenses
            WHERE is_active = true
            """
        )
        
        for rec in recurring:
            try:
                # Determine if we should generate an expense today
                should_generate = False
                expense_date = today
                
                last_gen = rec['last_generated_date']
                start_date = rec['start_date']
                
                if rec['frequency'] == 'monthly':
                    # Generate on the same day of month as start_date
                    if today.day == start_date.day:
                        # Check if not already generated this month
                        if not last_gen or (last_gen.year != today.year or last_gen.month != today.month):
                            should_generate = True
                
                elif rec['frequency'] == 'weekly':
                    # Generate every 7 days from start_date
                    if not last_gen:
                        # First generation
                        if today >= start_date:
                            should_generate = True
                    else:
                        days_since_last = (today - last_gen).days
                        if days_since_last >= 7:
                            should_generate = True
                
                if should_generate:
                    # Create the expense
                    await db.execute(
                        """
                        INSERT INTO expenses 
                        (user_id, category_id, amount, currency, expense_date, description,
                         original_currency, converted_amount, conversion_rate)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 1.0)
                        """,
                        rec['user_id'], rec['category_id'], rec['amount'], rec['currency'],
                        expense_date, f"[Recurring] {rec['description']}" if rec['description'] else "[Recurring]",
                        rec['currency'], rec['amount']
                    )
                    
                    # Update last_generated_date
                    await db.execute(
                        """
                        UPDATE recurring_expenses
                        SET last_generated_date = $1, updated_at = now()
                        WHERE id = $2
                        """,
                        expense_date, rec['id']
                    )
                    
                    logger.info(f"Generated recurring expense {rec['id']} for user {rec['user_id']}")
            
            except Exception as e:
                logger.error(f"Error generating recurring expense {rec['id']}: {e}")
                continue
        
        logger.info("Recurring expenses generation job completed")
    
    except Exception as e:
        logger.error(f"Error in recurring expenses job: {e}")

def start_scheduler():
    """Start the background scheduler."""
    # Run daily at 00:01 AM
    scheduler.add_job(
        generate_recurring_expenses,
        'cron',
        hour=0,
        minute=1,
        id='generate_recurring_expenses'
    )
    
    scheduler.start()
    logger.info("Scheduler started - recurring expenses job scheduled for daily 00:01")

def shutdown_scheduler():
    """Shutdown the scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler shutdown")