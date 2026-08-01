FROM node:20

WORKDIR /app/frontend

ENV HOST=0.0.0.0 \
    PORT=3000

RUN npm install -g yarn

COPY package.json ./package.json

RUN yarn install

COPY . .

EXPOSE 3000

CMD ["yarn", "start"]