
# GET methods

## HTTP 200 (Ok)
A successful GET method typically returns HTTP status code 200 (OK). If the resource cannot be found, the method should return 404 (Not Found).

## HTTP 404 (Resource Not Found)
If the resource cannot be found, the method should return 404 (Not Found).

## HTTP 400 (Bad Request)
If the client puts invalid data into the request, the server should return HTTP status code 400 (Bad Request).The response body can contain additional information about the error or a link to a URI that provides more details.

## HTTP 500 (Internal Server Error)
If internal unhandled error occured, the method should return 404 (Not Found).

# POST methods

## HTTP 201 (Created)
If a POST method creates a new resource, it returns HTTP status code 201 (Created). The URI of the new resource is included in the Location header of the response. The response body contains a representation of the resource.

## HTTP 200 (Ok)

If the method does some processing but does not create a new resource, the method can return HTTP status code 200 and include the result of the operation in the response body.

## HTTP 204 (Not Found)
If there is no result to return, the method can return HTTP status code 204 (No Content) with no response body.

## HTTP 400 (Bad Request)
If the client puts invalid data into the request, the server should return HTTP status code 400 (Bad Request).The response body can contain additional information about the error or a link to a URI that provides more details.

## HTTP 500 (Internal Server Error)
If internal unhandled error occured, the method should return 404 (Not Found).

# PUT methods

## HTTP 201
If a PUT method creates a new resource, it returns HTTP status code 201 (Created), as with a POST method.

## HTTP 200
If the method updates an existing resource, it returns either 200 (OK)

## HTTP 400 (Bad Request)
If the client puts invalid data into the request, the server should return HTTP status code 400 (Bad Request).The response body can contain additional information about the error or a link to a URI that provides more details.

## HTTP 204
No Content

## HTTP 409
In some cases, it might not be possible to update an existing resource e.g.-request is valid, but the changes can't be applied to the resource in its current state. In that case, consider returning HTTP status code 409 (Conflict).

## HTTP 500 (Internal Server Error)
If internal unhandled error occured, the method should return 404 (Not Found).

# Delete methods

## HTTP 200 (Ok)
A successful DELETE method typically returns HTTP status code 200 (OK). If the resource cannot be found, the method should return 404 (Not Found).

## HTTP 404 (Resource Not Found)
If the resource cannot be found, the method should return 404 (Not Found).

## HTTP 400 (Bad Request)
If the client puts invalid data into the request, the server should return HTTP status code 400 (Bad Request).The response body can contain additional information about the error or a link to a URI that provides more details.

## HTTP 500 (Internal Server Error)
If internal unhandled error occured, the method should return 404 (Not Found).
