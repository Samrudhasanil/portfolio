import requests

# The URL of your running Flask app
url = 'http://127.0.0.1:5000/predict'

# Path to your test image
image_path = r'C:\Users\LOQ\Downloads\tes\test.jpg'

# Define the text payload and image file
data = {
    'text': 'Please help me, I am in danger and need assistance immediately.'
}

with open(image_path, 'rb') as f:
    files = {
        'image': ('test.jpg', f, 'image/jpeg')
    }
    
    # Send both text (form data) and image (files) in a single POST request
    response = requests.post(url, data=data, files=files)

print("Status Code:", response.status_code)
print("Response JSON:", response.json())