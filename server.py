from flask import Flask

app = Flask(__name__)

# Members API route
@app.route('/members')
def members():
    return {"members": ["member1", "member2", "member3"]}

@app.route('/api/nav_items')
def get_nav_items():
    return {"nav_items": ["Barber", "Salon kosmetyczny", "Paznokcie", "Masaż", "Zwierzęta", "Siłownia", "Więcej..."]}

def get_image_cards():
    return {"image_cards" : [
            {
                "imageSrc": "images/barber.jpg",
                "imageAlt": "Image 2",
                "description": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Ut pulvinar ipsum orci, eget ullamcorper lectus cursus nec."
            },
            {
                "imageSrc": "images/salon.jpg",
                "imageAlt": "Image 3",
                "description": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Ut pulvinar ipsum orci, eget ullamcorper lectus cursus nec."
            },
            {
                "imageSrc": "images/paznokcie.jpg",
                "imageAlt": "Image 4",
                "description": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Ut pulvinar ipsum orci, eget ullamcorper lectus cursus nec."
            },
            {
                "imageSrc": "https://cdn.builder.io/api/v1/image/assets/TEMP/b10e017e3fafc40f727425bb7f8f66387d777cb825bf4515f5163fb0909ca872?apiKey=d10d36f0508e433185a32e898689ca50&",
                "imageAlt": "Image 5",
                "description": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Ut pulvinar ipsum orci, eget ullamcorper lectus cursus nec."
            }
        ]
    }

if __name__ == '__main__':
    app.run(debug=True)