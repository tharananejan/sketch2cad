from fastapi import APIRouter, HTTPException
from typing import Union
from .schemas import StartRequest, ContinueRequest, DialogueResponse, CompleteResponse
from .session import session_manager
from .extractor import extract_shape, extract_parameters
from .checker import check_missing
from .dialogue import ask_missing_parameter

router = APIRouter(prefix="", tags=["parameter"])

@router.post("/start", response_model=Union[DialogueResponse, CompleteResponse])
async def start_session(request: StartRequest):
    """
    Initializes a new conversation session to collect shape parameters.
    """
    shape = extract_shape(request.message)
    if not shape:
        raise HTTPException(status_code=400, detail="Could not detect a supported shape.")
        
    session_id = session_manager.create_session()
    
    # Check all required parameters for the shape first
    all_missing_params = check_missing(shape, {})
    
    # Try to extract any initially provided parameters
    try:
        parameters = extract_parameters(request.message, all_missing_params)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Recalculate missing parameters after extraction
    missing_params = check_missing(shape, parameters)
    
    session_manager.update_session(session_id, {
        "shape": shape,
        "parameters": parameters,
        "missing": missing_params
    })
    session_manager.add_to_history(session_id, "user", request.message)
    
    if len(missing_params) == 0:
        session_manager.delete_session(session_id)
        return CompleteResponse(shape=shape, parameters=parameters)
        
    next_missing = missing_params[0]
    reply = ask_missing_parameter(shape, parameters, next_missing)
    
    session_manager.add_to_history(session_id, "assistant", reply)
    
    return DialogueResponse(session_id=session_id, reply=reply, status="waiting")

@router.post("/continue", response_model=Union[DialogueResponse, CompleteResponse])
async def continue_session(request: ContinueRequest):
    """
    Continues an existing session to collect the next missing parameter.
    """
    session = session_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Invalid session ID.")
        
    shape = session["shape"]
    current_params = session["parameters"]
    current_missing = session["missing"]
    
    session_manager.add_to_history(request.session_id, "user", request.message)
    
    # Extract any parameters from the latest message
    try:
        extracted = extract_parameters(request.message, current_missing)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    current_params.update(extracted)
    
    # Recalculate missing parameters
    new_missing = check_missing(shape, current_params)
    
    session_manager.update_session(request.session_id, {
        "parameters": current_params,
        "missing": new_missing
    })
    
    if len(new_missing) == 0:
        session_manager.delete_session(request.session_id)
        return CompleteResponse(shape=shape, parameters=current_params)
        
    next_missing = new_missing[0]
    reply = ask_missing_parameter(shape, current_params, next_missing)
    
    session_manager.add_to_history(request.session_id, "assistant", reply)
    
    return DialogueResponse(session_id=request.session_id, reply=reply, status="waiting")
