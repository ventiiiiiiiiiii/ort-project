let image = document.getElementById('memes');
let myPics = ["/static/images/memes/meme1.jpg", "/static/images/memes/meme2.jpg", "/static/images/memes/meme3.jpg", "/static/images/memes/meme4.jpg", "/static/images/memes/meme5.jpg", "/static/images/memes/meme6.jpg", "/static/images/memes/meme7.jpg", "/static/images/memes/meme8.jpg", "/static/images/memes/meme9.jpg", "/static/images/memes/meme10.jpg", "/static/images/memes/meme11.jpg", "/static/images/memes/meme12.jpg", "/static/images/memes/meme13.jpg", "/static/images/memes/meme14.jpg", "/static/images/memes/meme15.jpg"];
let res = () => {
  randomNum = Math.floor(Math.random() * myPics.length);
  image.src = myPics[randomNum];
  console.log(image.src);
}
res();
