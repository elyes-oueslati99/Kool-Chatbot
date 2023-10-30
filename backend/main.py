from fastapi import FastAPI, Request
from fastapi.responses import  JSONResponse
import db_helper
import generic_helper
app = FastAPI()

inprogress_orders={}

@app.post("/")
async def handle_request(request: Request):
    # Retrieve the JSON data from the request
    payload = await request.json()

    # # Log the entire payload for debugging
    # print("Full Payload:", payload)
    intent = payload['queryResult']['intent']['displayName']
    parameters = payload['queryResult']['parameters']
    output_contexts = payload['queryResult']['outputContexts']
    session_str=output_contexts[0]["name"]
    session_id=generic_helper.extract_session_id(session_str)
    intent_handler_dict = {
        'order.add-context: ongoing-order': add_to_order,
        'order.remove - context: ongoing-order': remove_from_order,
        'order.complete - context: ongoing-order': complete_order,
        'track.order - context: ongoing-tracking': track_order
    }

    return intent_handler_dict[intent](parameters,session_id)


def add_to_order(parameters: dict,session_id: str):
    food_items=parameters['food-item']
    quantities=parameters['number']
    if len(quantities)!=len(food_items):
        fulfillment_text="sorry order not clear. Please specify a quantity for each food item"
    else:
        # Create the dictionary using zip and dict
        new_food_dict = dict(zip(food_items, quantities))
        if session_id in inprogress_orders:
            cur_food_dic=inprogress_orders[session_id]
            cur_food_dic.update(new_food_dict)
            inprogress_orders[session_id]=cur_food_dic
        else:
            inprogress_orders[session_id]=new_food_dict
        order_str=generic_helper.get_str_from_food_dict(inprogress_orders[session_id])
        print("*******************")
        print(inprogress_orders)
        fulfillment_text=f"So far you have: {order_str} do you need anything else."
    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })
def complete_order(parameters: dict, session_id: str):
    if session_id not in inprogress_orders:
        fulfillment_text="I am having trouble finding your order. Sorry! can you place a new order"
    else:
        order=inprogress_orders[session_id]
        order_id=save_to_db(order)
        if order_id==-1:
            fulfillment_text = "Sorry, I couldn't process your order due to a backend error. " \
                               "Please place a new order again"
        else:
            order_total = db_helper.get_total_order_price(order_id)

            fulfillment_text = f"Awesome. We have placed your order. " \
                               f"Here is your order id # {order_id}. " \
                               f"Your order total is {order_total} which you can pay at the time of delivery!"

        del inprogress_orders[session_id]
    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })

def save_to_db(order):
    next_order_id=db_helper.get_next_order_id()
    for food_item, quantity in order.items():
        rcode=db_helper.insert_order_item(
            food_item,
            quantity,
            next_order_id
        )
        if rcode==-1:
            return -1
    # Now insert order tracking status
    db_helper.insert_order_tracking(next_order_id, "in progress")

    return next_order_id
# inprogress_orders={
#     sess_id1={pizza:1},
# sess_id2={chapati:1,mlewi:2}
# }
#step1 locate the session_id
#get the value from the dict {"chapati:1,mlewi:2}
#remove the food items. request ['melwi']
def remove_from_order(parameters: dict, session_id: str):

    if session_id not in inprogress_orders:
        return JSONResponse(content={
            "fulfillmentText":"I am having trouble finding your order. Sorry! can you place a new order"
        })
    curr_order=inprogress_orders[session_id]
    food_items=parameters["food-item"]

    no_such_items=[]
    removed_items=[]
    for item in food_items:
        if item not in curr_order:
            no_such_items.append(item)
        else:
            removed_items.append(item)
            del curr_order[item]
    if len(removed_items)>0:
            fulfillment_text = f'Removed {",".join(removed_items)} from your order!'
    if len(no_such_items)>0:
            fulfillment_text = f' Your current order does not have {",".join(no_such_items)}.'

    if len(curr_order.keys())==0:
            fulfillment_text += " Your order is empty!"
    else:
            order_str=generic_helper.get_str_from_food_dict(curr_order)
            fulfillment_text +=f" Here is what is left in your order: {order_str}"
    return JSONResponse(content={
                        "fulfillmentText":fulfillment_text})




def track_order(parameters: dict,session_id:str):
    order_id=int(parameters['number'])
    order_status=db_helper.get_order_status(order_id)
    if order_status:
        fulfillment_text = f"The order status for order id: {order_id} is: {order_status}"
    else:
        fulfillment_text = f"No order found with order id: {order_id}"

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })

