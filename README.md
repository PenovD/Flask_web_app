 Application for analyzing user costs.
 Flask app with 3 endpoints and integration with Telegram BOT.



GET Method

/total_spent/<int:user_id>   

/total_spent/599
{
    "total_spent": 15813.390000000001,
    "user_id": 599
}

GET Method

/average_spending_by_age     
{
    "18-24": 2509.7405273833674,
    "25-30": 2471.584902193242,
    "31-36": 2529.1548323576367,
    "37-47": 2495.8429822335024,
    ">47": 2485.7710634441087
}






POST Method.

/write_high_spending_user    
{    
    "user_id": 1,
    "total_spending": 2000
}




Other apps used for this project are Postman, Telegram.
