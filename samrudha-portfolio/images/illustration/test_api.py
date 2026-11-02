import requests

# The URL of your running Flask app
url = 'http://127.0.0.1:5000/predict'

# Path to the test image you saw earlier in your folder
image_path = r'C:\Users\LOQ\Downloads\tes\test.jpg'

# Send the image file in a POST request
with open(image_path, 'rb') as f:
    files = {'image': f}
    response = requests.post(url, files=files)

print("Status Code:", response.status_code)
print("Response JSON:", response.json())